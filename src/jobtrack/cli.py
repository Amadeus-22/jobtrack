"""Command line entry point.

Subcommands are thin: they parse arguments, call one function, and print. All
the thinking lives in `metrics` and `report`, which are pure and testable
without a terminal.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from . import metrics, report, store
from .model import Application, Event, Outcome, Seniority, Stage

# Technologies I can claim in an interview without flinching. Anything a posting
# asks for that is not here shows up in the "skills I do not have" report.
KNOWN_STACK = {
    "python", "go", "golang", "php", "laravel", "javascript", "typescript", "react",
    "sql", "mysql", "postgresql", "sqlite", "django", "pandas", "scikit-learn",
    "docker", "git", "linux", "bash", "rest", "rest api", "github actions",
    "gitlab ci", "aws ec2", "n8n", "zapier", "three.js", "pytest", "systemd",
}


def _today(value: str | None) -> date:
    return date.fromisoformat(value) if value else date.today()


def cmd_add(args: argparse.Namespace) -> int:
    app = Application(
        id=args.id,
        company=args.company,
        role=args.role,
        applied_on=_today(args.date),
        channel=args.channel,
        seniority=Seniority(args.seniority),
        stack=tuple(args.stack or []),
        resume=args.resume or "",
        asked_salary=args.salary,
        currency=args.currency,
        remote=not args.onsite,
        notes=args.notes or "",
    )
    store.append(app, args.path)
    print(f"recorded {app.id}: {app.company} — {app.role}")
    return 0


def cmd_event(args: argparse.Namespace) -> int:
    applications = store.load(args.path)
    updated: list[Application] = []
    found = False
    for app in applications:
        if app.id == args.id:
            found = True
            event = Event(on=_today(args.date), stage=Stage(args.stage), note=args.note or "")
            outcome = Outcome(args.outcome) if args.outcome else app.outcome
            app = Application(
                id=app.id, company=app.company, role=app.role, applied_on=app.applied_on,
                channel=app.channel, seniority=app.seniority, stack=app.stack,
                resume=app.resume, asked_salary=app.asked_salary, currency=app.currency,
                remote=app.remote, events=app.events + (event,), outcome=outcome,
                notes=app.notes,
            )
        updated.append(app)
    if not found:
        print(f"no application with id {args.id!r}", file=sys.stderr)
        return 1
    store.save_all(updated, args.path)
    print(f"{args.id}: {args.stage}")
    return 0


def cmd_stats(args: argparse.Namespace) -> int:
    applications = store.load(args.path)
    if not applications:
        print("no applications recorded yet")
        return 0
    today = _today(args.date)
    print(f"applications        {len(applications)}")
    print(f"answered            {metrics.response_rate(applications)}")
    print(f"interviewed         {metrics.interview_rate(applications)}")
    print(f"offers              {metrics.offer_rate(applications)}")
    delay = metrics.median_days_to_answer(applications)
    print(f"median days to reply {delay if delay is not None else '—'}")
    print(f"stale (21d+)        {len(metrics.stale(applications, today))}")
    for currency in sorted({a.currency for a in applications}):
        asked = metrics.salary_asked(applications, currency)
        if asked:
            low, high, mid = asked
            print(f"asked in {currency:<4}       min {low} / median {mid:.0f} / max {high}")
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    applications = store.load(args.path)
    print(report.render(applications, _today(args.date), KNOWN_STACK))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    applications = store.load(args.path)
    print(f"{len(applications)} records, all valid")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jobtrack", description=__doc__)
    parser.add_argument("--path", type=Path, default=store.DEFAULT_PATH,
                        help="application log (default: data/applications.jsonl)")
    parser.add_argument("--date", help="treat this ISO date as today (for reproducible reports)")
    sub = parser.add_subparsers(dest="command", required=True)

    add = sub.add_parser("add", help="record a new application")
    add.add_argument("--id", required=True)
    add.add_argument("--company", required=True)
    add.add_argument("--role", required=True)
    add.add_argument("--channel", default="linkedin")
    add.add_argument("--seniority", default="unspecified",
                     choices=[s.value for s in Seniority])
    add.add_argument("--stack", nargs="*", help="technologies the posting asked for")
    add.add_argument("--resume", help="which CV variant was sent")
    add.add_argument("--salary", type=int, help="salary asked for")
    add.add_argument("--currency", default="BRL")
    add.add_argument("--onsite", action="store_true")
    add.add_argument("--notes")
    add.set_defaults(func=cmd_add)

    event = sub.add_parser("event", help="append a stage change to an application")
    event.add_argument("--id", required=True)
    event.add_argument("--stage", required=True, choices=[s.value for s in Stage])
    event.add_argument("--outcome", choices=[o.value for o in Outcome])
    event.add_argument("--note")
    event.set_defaults(func=cmd_event)

    stats = sub.add_parser("stats", help="print headline metrics")
    stats.set_defaults(func=cmd_stats)

    rep = sub.add_parser("report", help="print the weekly report")
    rep.set_defaults(func=cmd_report)

    val = sub.add_parser("validate", help="check every record in the log")
    val.set_defaults(func=cmd_validate)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except store.StoreError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
