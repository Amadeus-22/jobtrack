"""Reading and writing the application log.

The store is a JSON Lines file under version control: one application per line,
appended over time. That choice buys three things a database would not. The
history is a git history, so "what did I believe last month" is `git log`. A
single line can be fixed in any text editor when a date is wrong at midnight.
And the tool runs anywhere Python runs, with nothing to install.

Records are validated on the way in, not on the way out: a malformed line fails
loudly at load time, naming the line number, instead of silently producing a
metric nobody can trust.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .model import Application, Event, Outcome, Seniority, Stage

DEFAULT_PATH = Path("data/applications.jsonl")


class StoreError(Exception):
    """Raised when the log on disk cannot be trusted."""


def _parse_date(value: str, field: str, line_no: int) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise StoreError(f"line {line_no}: {field} is not an ISO date: {value!r}") from exc


def _application_from_dict(raw: dict, line_no: int) -> Application:
    try:
        events = tuple(
            Event(
                on=_parse_date(e["on"], "event.on", line_no),
                stage=Stage(e["stage"]),
                note=e.get("note", ""),
            )
            for e in raw.get("events", [])
        )
        return Application(
            id=raw["id"],
            company=raw["company"],
            role=raw["role"],
            applied_on=_parse_date(raw["applied_on"], "applied_on", line_no),
            channel=raw.get("channel", "unknown"),
            seniority=Seniority(raw.get("seniority", "unspecified")),
            stack=tuple(raw.get("stack", [])),
            resume=raw.get("resume", ""),
            asked_salary=raw.get("asked_salary"),
            currency=raw.get("currency", "BRL"),
            remote=raw.get("remote", True),
            events=events,
            outcome=Outcome(raw.get("outcome", "pending")),
            notes=raw.get("notes", ""),
        )
    except KeyError as exc:
        raise StoreError(f"line {line_no}: missing required field {exc.args[0]!r}") from exc
    except ValueError as exc:
        raise StoreError(f"line {line_no}: {exc}") from exc


def _application_to_dict(app: Application) -> dict:
    payload = {
        "id": app.id,
        "company": app.company,
        "role": app.role,
        "applied_on": app.applied_on.isoformat(),
        "channel": app.channel,
        "seniority": app.seniority.value,
        "stack": list(app.stack),
        "resume": app.resume,
        "asked_salary": app.asked_salary,
        "currency": app.currency,
        "remote": app.remote,
        "events": [
            {"on": e.on.isoformat(), "stage": e.stage.value, "note": e.note}
            for e in app.events
        ],
        "outcome": app.outcome.value,
        "notes": app.notes,
    }
    return {k: v for k, v in payload.items() if v not in (None, "", [], ())}


def load(path: Path = DEFAULT_PATH) -> list[Application]:
    """Read every application, or fail naming the line that broke."""
    if not path.exists():
        return []
    applications: list[Application] = []
    seen: set[str] = set()
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("//"):
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError as exc:
            raise StoreError(f"line {line_no}: invalid JSON: {exc.msg}") from exc
        app = _application_from_dict(raw, line_no)
        if app.id in seen:
            raise StoreError(f"line {line_no}: duplicate application id {app.id!r}")
        seen.add(app.id)
        applications.append(app)
    return applications


def append(app: Application, path: Path = DEFAULT_PATH) -> None:
    """Add one application to the log, refusing to duplicate an id."""
    existing = {a.id for a in load(path)}
    if app.id in existing:
        raise StoreError(f"application id {app.id!r} already exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(_application_to_dict(app), ensure_ascii=False) + "\n")


def save_all(applications: list[Application], path: Path = DEFAULT_PATH) -> None:
    """Rewrite the whole log. Used when an existing record changes stage."""
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(
        json.dumps(_application_to_dict(a), ensure_ascii=False) for a in applications
    )
    path.write_text(body + "\n" if body else "", encoding="utf-8")
