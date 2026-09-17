#!/usr/bin/env python3
"""Write rows to audit/jev-me.sqlite. Does not call Jev. Does not apply gates."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUDIT_DIR = Path(__file__).resolve().parent
DB_PATH = AUDIT_DIR / "jev-me.sqlite"
SCHEMA_PATH = AUDIT_DIR / "schema.sql"
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
PHASES = (
    "open",
    "weigh_pool",
    "ask",
    "weigh_answers",
    "close",
    "confirm",
    "abandon",
)
KINDS = ("jev_call", "gate", "utterance", "fact", "note")
STATUSES = ("open", "closed", "abandoned")
LOG_SECTIONS = (
    ("settle", "Settled"),
    ("pushback", "Pushed back"),
    ("fact", "Looked up"),
    ("prune", "Not asked"),
    ("hold", "Waiting on another call"),
    ("reframe", "Needs a better question"),
    ("survivor", "Still open"),
    ("reopen", "Would reopen"),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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


def connect() -> sqlite3.Connection:
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return conn


def start(subject: str) -> str:
    subject = subject.strip()
    if not subject:
        raise ValueError("subject must be a non-empty string")
    session_id = uuid.uuid4().hex[:12]
    with connect() as conn:
        conn.execute(
            "INSERT INTO sessions (id, subject, status, started_at) VALUES (?, ?, 'open', ?)",
            (session_id, subject, utc_now()),
        )
    return session_id


def add_event(
    session_id: str,
    phase: str,
    kind: str,
    payload: dict[str, Any],
    candidate_id: str | None,
) -> None:
    if phase not in PHASES:
        raise ValueError(f"phase must be one of {PHASES}")
    if kind not in KINDS:
        raise ValueError(f"kind must be one of {KINDS}")
    body = json.dumps(redact(payload), ensure_ascii=True, sort_keys=True)
    with connect() as conn:
        exists = conn.execute(
            "SELECT 1 FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if exists is None:
            raise FileNotFoundError(f"unknown session {session_id}")
        conn.execute(
            "INSERT INTO events (session_id, at, phase, kind, candidate_id, payload) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (session_id, utc_now(), phase, kind, candidate_id, body),
        )


def set_status(session_id: str, status: str) -> None:
    if status not in STATUSES:
        raise ValueError("status must be open, closed, or abandoned")
    closed_at = utc_now() if status in {"closed", "abandoned"} else None
    with connect() as conn:
        cur = conn.execute(
            "UPDATE sessions SET status = ?, closed_at = COALESCE(?, closed_at) WHERE id = ?",
            (status, closed_at, session_id),
        )
        if cur.rowcount == 0:
            raise FileNotFoundError(f"unknown session {session_id}")


def list_sessions(status: str | None) -> list[dict[str, Any]]:
    if status is not None and status not in STATUSES:
        raise ValueError("status must be open, closed, or abandoned")
    sql = "SELECT id, subject, status, started_at, closed_at FROM sessions"
    params: tuple[str, ...] = ()
    if status is not None:
        sql += " WHERE status = ?"
        params = (status,)
    sql += " ORDER BY started_at DESC"
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def _text(payload: dict[str, Any], *keys: str) -> str:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _item_line(item: dict[str, str]) -> str:
    title = item.get("title") or ""
    ident = item.get("id") or ""
    if title and title != ident:
        head = f"**{title}**"
    elif title:
        head = f"**{title}**"
    elif ident:
        head = ""
    else:
        head = "**Untitled**"
    answer = item.get("answer") or item.get("text") or ""
    reason = item.get("reason") or ""
    parts = [part for part in (head, answer) if part]
    line = "- " + " ".join(parts) if parts else "- Untitled"
    if reason:
        line += f" — {reason}"
    return line


def render_log(session_id: str) -> str:
    with connect() as conn:
        session = conn.execute(
            "SELECT * FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if session is None:
            raise FileNotFoundError(f"unknown session {session_id}")
        rows = conn.execute(
            "SELECT kind, candidate_id, payload FROM events "
            "WHERE session_id = ? ORDER BY id",
            (session_id,),
        ).fetchall()

    by_id: dict[str, dict[str, str]] = {}
    facts: list[dict[str, str]] = []
    for row in rows:
        payload = json.loads(row["payload"])
        if not isinstance(payload, dict):
            continue
        kind = row["kind"]
        cid = row["candidate_id"] or _text(payload, "id")
        if kind == "jev_call":
            continue
        if kind == "utterance":
            if not cid:
                continue
            item = by_id.setdefault(cid, {"id": cid, "gate": "survivor"})
            item["answer"] = _text(payload, "text", "answer") or item.get("answer", "")
            continue
        if kind == "fact":
            fact_item = {
                "id": cid,
                "title": _text(payload, "title"),
                "text": _text(payload, "text", "answer"),
                "gate": "fact",
            }
            if cid:
                item = by_id.setdefault(cid, {"id": cid})
                item["gate"] = "fact"
                title = _text(payload, "title")
                if title:
                    item["title"] = title
                item["text"] = fact_item["text"]
            else:
                facts.append(fact_item)
            continue
        if kind != "gate":
            continue
        if not cid:
            continue
        item = by_id.setdefault(cid, {"id": cid})
        new_gate = (
            _text(payload, "gate") or item.get("gate") or "survivor"
        ).lower()
        if new_gate != item.get("gate"):
            item.pop("reason", None)
        item["gate"] = new_gate
        title = _text(payload, "title")
        if title:
            item["title"] = title
        elif "title" not in item:
            item["title"] = ""
        answer = _text(payload, "answer", "text")
        if answer:
            item["answer"] = answer
        reason = _text(payload, "reason")
        if reason:
            item["reason"] = reason

    lines = [
        f"# {session['subject']}",
        "",
        "Confirmation of this log is not a license to implement.",
        "",
    ]
    grouped: dict[str, list[dict[str, str]]] = {key: [] for key, _ in LOG_SECTIONS}
    for item in by_id.values():
        gate = item.get("gate") or "survivor"
        grouped.setdefault(gate, []).append(item)
    grouped["fact"].extend(facts)

    any_section = False
    for gate, heading in LOG_SECTIONS:
        items = grouped.get(gate) or []
        if not items:
            continue
        any_section = True
        lines.append(f"## {heading}")
        for item in items:
            lines.append(_item_line(item))
        lines.append("")
    if not any_section:
        lines.append("No decisions recorded yet.")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _read_payload(raw: str) -> dict[str, Any]:
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("payload must be a JSON object")
    return data


def _payload_from_args(json_text: str | None, payload_path: str | None) -> dict[str, Any]:
    if json_text is not None and payload_path is not None:
        raise ValueError("pass --json or --payload, not both")
    if json_text is not None:
        return _read_payload(json_text)
    if payload_path is None:
        raise ValueError("pass --json '{...}' or --payload FILE (use - for stdin)")
    raw = sys.stdin.read() if payload_path == "-" else Path(payload_path).read_text(
        encoding="utf-8"
    )
    return _read_payload(raw)


def _print_json(value: Any) -> None:
    json.dump(value, sys.stdout, ensure_ascii=True, sort_keys=True)
    sys.stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    start_p = sub.add_parser("start", help="Create a session")
    start_p.add_argument("--subject", required=True)

    event_p = sub.add_parser(
        "event",
        help="Append one event",
        epilog="Example: write.py event --session ID --phase ask --kind utterance --json '{\"text\":\"Stay on Render.\"}'",
    )
    event_p.add_argument("--session", required=True)
    event_p.add_argument("--phase", required=True, choices=PHASES)
    event_p.add_argument("--kind", required=True, choices=KINDS)
    event_p.add_argument("--candidate")
    event_p.add_argument(
        "--json",
        dest="json_text",
        metavar="JSON",
        help="JSON object as a string",
    )
    event_p.add_argument(
        "--payload",
        help="JSON file, or - for stdin. Do not write this file into the user's project.",
    )

    status_p = sub.add_parser("status", help="Set session status")
    status_p.add_argument("--session", required=True)
    status_p.add_argument("--to", required=True, choices=STATUSES)

    log_p = sub.add_parser("log", help="Print the human decision log")
    log_p.add_argument("--session", required=True)

    list_p = sub.add_parser("list", help="List sessions")
    list_p.add_argument("--status", choices=STATUSES)

    args = parser.parse_args(argv)
    try:
        if args.cmd == "start":
            session_id = start(args.subject)
            json.dump({"session_id": session_id, "db": str(DB_PATH)}, sys.stdout)
            sys.stdout.write("\n")
            return 0
        if args.cmd == "event":
            add_event(
                args.session,
                args.phase,
                args.kind,
                _payload_from_args(args.json_text, args.payload),
                args.candidate,
            )
            _print_json({"ok": True})
            return 0
        if args.cmd == "status":
            set_status(args.session, args.to)
            _print_json({"ok": True, "status": args.to})
            return 0
        if args.cmd == "list":
            _print_json(list_sessions(args.status))
            return 0
        sys.stdout.write(render_log(args.session))
        return 0
    except (ValueError, FileNotFoundError, json.JSONDecodeError, OSError) as exc:
        _print_json({"error": str(exc)})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
