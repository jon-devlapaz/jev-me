#!/usr/bin/env python3
"""Call Jev. Does not write sqlite. Does not apply gates."""

from __future__ import annotations

import json
import sys
from typing import Any

import msgspec
from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

MODEL = "jev-1.13.0"
SECRET_KEYS = frozenset(
    {
        "api_key",
        "apikey",
        "typesafe_api_key",
        "authorization",
        "password",
        "secret",
        "token",
        "access_token",
    }
)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        out = {}
        for key, inner in value.items():
            if str(key).lower() in SECRET_KEYS:
                out[key] = "[redacted]"
            else:
                out[key] = redact(inner)
        return out
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        lowered = value.lower()
        if "typesafe_api_key" in lowered or "api_key=" in lowered:
            return "[redacted]"
    return value


def to_question(spec: dict[str, Any]) -> Noul | Score | Choice:
    if not isinstance(spec, dict):
        raise ValueError("question must be an object")
    kind = spec.get("type")
    instructions = spec.get("instructions")
    criteria = spec.get("criteria")
    if kind == "noul":
        kwargs: dict[str, Any] = {"instructions": instructions}
        if criteria is not None:
            kwargs["criteria"] = criteria
        return Noul(**kwargs)
    if kind == "score":
        return Score(instructions=instructions, criteria=criteria)
    if kind == "choice":
        return Choice(instructions=instructions, criteria=criteria)
    raise ValueError(f"question type must be noul, score, or choice, not {kind!r}")


def serialize(resp: Any) -> dict[str, Any]:
    payload = msgspec.to_builtins(resp)
    if not isinstance(payload, dict):
        raise TypeError("Jev response was not an object")
    return payload


def main() -> int:
    raw = sys.stdin.read()
    if not raw.strip():
        json.dump({"error": "stdin is empty; pass {state, questions}"}, sys.stdout)
        sys.stdout.write("\n")
        return 1
    try:
        body = json.loads(raw)
        if not isinstance(body, dict):
            raise ValueError("payload must be an object")
        state = body["state"]
        specs = body["questions"]
        if not isinstance(specs, dict) or not specs:
            raise ValueError("questions must be a non-empty object")
        model = body.get("model", MODEL)
        if model != MODEL:
            raise ValueError(f"model must be {MODEL}; do not fall back")
        questions = {qid: to_question(spec) for qid, spec in specs.items()}
        try:
            with TypeSafeClient(model=MODEL) as client:
                resp = client.system_one(state, questions, model=MODEL)
        except Exception as exc:
            json.dump({"error": str(exc)}, sys.stdout)
            sys.stdout.write("\n")
            return 1
        payload = serialize(resp)
        answers = payload.get("answers")
        returned = payload.get("model")
        json.dump(
            redact({"model": returned, "answers": answers}),
            sys.stdout,
            ensure_ascii=True,
            sort_keys=True,
        )
        sys.stdout.write("\n")
        return 0
    except (KeyError, TypeError, ValueError, json.JSONDecodeError, OSError) as exc:
        json.dump({"error": str(exc)}, sys.stdout)
        sys.stdout.write("\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
