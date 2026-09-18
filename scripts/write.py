#!/usr/bin/env python3
"""Write rows to scripts/jev-me.sqlite. Does not call Jev. Does not apply gates."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
DB_PATH = SCRIPT_DIR / "jev-me.sqlite"
SCHEMA_PATH = SCRIPT_DIR / "schema.sql"
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
    ("survivor", "Still open"),
    ("reopen", "Would reopen"),
)
KNOWN_SECTIONS = {key for key, _ in LOG_SECTIONS}


@dataclass
class Item:
    id: str
    title: str = ""
    body: str = ""
    reason: str = ""
    section: str = "survivor"


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
    SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
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
    if kind == "gate":
        if not (candidate_id and candidate_id.strip()):
            raise ValueError("gate requires --candidate")
        gate_name = payload.get("gate")
        if not isinstance(gate_name, str) or not gate_name.strip():
            raise ValueError("gate payload requires gate")
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
            "UPDATE sessions SET status = ?, closed_at = ? WHERE id = ?",
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


def _item_line(item: Item) -> str:
    if item.title:
        line = f"- **{item.title}** {item.body}".rstrip() if item.body else f"- **{item.title}**"
    elif item.body:
        line = f"- {item.body}"
    else:
        line = f"- **{item.id or 'Untitled'}**"
    if item.reason:
        line += f" — {item.reason}"
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

    by_id: dict[str, Item] = {}
    facts: list[Item] = []
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
            item = by_id.setdefault(cid, Item(id=cid))
            item.body = _text(payload, "text", "answer") or item.body
            continue
        if kind == "fact":
            title = _text(payload, "title")
            body = _text(payload, "text", "answer")
            if cid:
                item = by_id.setdefault(cid, Item(id=cid))
                item.section = "fact"
                if title:
                    item.title = title
                item.body = body
            else:
                facts.append(Item(id="", title=title, body=body, section="fact"))
            continue
        if kind != "gate" or not cid:
            continue
        item = by_id.setdefault(cid, Item(id=cid))
        new_section = _text(payload, "gate").lower()
        if not new_section:
            continue
        if new_section not in KNOWN_SECTIONS:
            new_section = "survivor"
        if new_section != item.section:
            item.reason = ""
        item.section = new_section
        title = _text(payload, "title")
        if title:
            item.title = title
        answer = _text(payload, "answer", "text")
        if answer:
            item.body = answer
        reason = _text(payload, "reason")
        if reason:
            item.reason = reason

    lines = [
        f"# {session['subject']}",
        "",
        "Confirmation of this log is not a license to implement.",
        "",
    ]
    grouped: dict[str, list[Item]] = {key: [] for key, _ in LOG_SECTIONS}
    for item in by_id.values():
        grouped.setdefault(item.section, []).append(item)
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


def render_review(session_id: str | None) -> str:
    with connect() as conn:
        if session_id:
            session = conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if session is None:
                raise FileNotFoundError(f"unknown session {session_id}")
            sessions = [session]
        else:
            sessions = conn.execute(
                "SELECT * FROM sessions WHERE status = 'closed' ORDER BY started_at"
            ).fetchall()
        if not sessions:
            return "No closed sessions.\n"
        ids = [row["id"] for row in sessions]
        placeholders = ",".join("?" * len(ids))
        events = conn.execute(
            "SELECT session_id, candidate_id, payload FROM events "
            f"WHERE session_id IN ({placeholders}) AND kind = 'gate' ORDER BY session_id, id",
            ids,
        ).fetchall()

    history: dict[tuple[str, str], list[str]] = {}
    for row in events:
        payload = json.loads(row["payload"])
        if not isinstance(payload, dict):
            continue
        cid = row["candidate_id"] or _text(payload, "id")
        gate = _text(payload, "gate").lower()
        if not cid or not gate:
            continue
        history.setdefault((row["session_id"], cid), []).append(gate)

    prune_n = settle_n = prune_back = settle_back = 0
    for gates in history.values():
        if "prune" in gates:
            prune_n += 1
            later = gates[gates.index("prune") + 1 :]
            if "reopen" in later:
                prune_back += 1
        if "settle" in gates:
            settle_n += 1
            later = gates[gates.index("settle") + 1 :]
            if "reopen" in later:
                settle_back += 1

    n_sessions = len(sessions)
    lines = [
        "# Review",
        "",
        f"{n_sessions} session(s) · {prune_n} pruned · {prune_back} brought back · "
        f"{settle_n} settled · {settle_back} unlocked",
        "",
        "Prune reversals grade the 0.8 discard bar. Settle reversals grade the 0.8 lock bar.",
        "",
    ]
    enough = n_sessions >= 3 or prune_n >= 10 or settle_n >= 10
    if not enough:
        lines.append("Too few closed sessions to move a bar. Do not edit the table.")
    elif prune_back or settle_back:
        lines.append(
            "Reversals showed up. Tell the person. Do not edit the table unless they say so."
        )
    else:
        lines.append("No reversals. Leave the table.")
    lines.append("")
    return "\n".join(lines)


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
    if payload_path is None or payload_path == "-":
        return _read_payload(sys.stdin.read())
    return _read_payload(Path(payload_path).read_text(encoding="utf-8"))


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
        epilog="Example: write.py event --session ID --phase ask --kind utterance <<'JSON'\\n{\"text\":\"We'll stay on Render.\"}\\nJSON",
    )
    event_p.add_argument("--session", required=True)
    event_p.add_argument("--phase", required=True, choices=PHASES)
    event_p.add_argument("--kind", required=True, choices=KINDS)
    event_p.add_argument("--candidate")
    event_p.add_argument(
        "--json",
        dest="json_text",
        metavar="JSON",
        help="JSON object as a string. Prefer stdin; quotes in answers will break this.",
    )
    event_p.add_argument(
        "--payload",
        help="JSON file, or - for stdin. Default is stdin. Do not write this file into the user's project.",
    )

    status_p = sub.add_parser("status", help="Set session status")
    status_p.add_argument("--session", required=True)
    status_p.add_argument("--to", required=True, choices=STATUSES)

    log_p = sub.add_parser("log", help="Print the human decision log")
    log_p.add_argument("--session", required=True)

    list_p = sub.add_parser("list", help="List sessions")
    list_p.add_argument("--status", choices=STATUSES)

    review_p = sub.add_parser("review", help="Grade prune and settle bars from closed sessions")
    review_p.add_argument("--session", help="One session; default is all closed sessions")

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
        if args.cmd == "review":
            sys.stdout.write(render_review(args.session))
            return 0
        if args.cmd == "log":
            sys.stdout.write(render_log(args.session))
            return 0
        parser.error(f"unknown command {args.cmd}")
    except (ValueError, FileNotFoundError, json.JSONDecodeError, OSError, sqlite3.Error) as exc:
        payload = {"error": str(exc)}
        _print_json(payload)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
