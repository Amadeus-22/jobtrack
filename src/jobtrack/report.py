"""Turning metrics into a weekly page a human will actually read.

The report answers four questions in order: how much did I send, what came
back, what is blocking me, and what should I do next week. Anything that does
not serve one of those four is left out, because a report nobody finishes is
worse than no report.
"""
from __future__ import annotations

from datetime import date

from . import metrics
from .model import Application, Outcome, Stage


def _bar(rate: metrics.Rate, width: int = 20) -> str:
    filled = round(rate.value * width)
    return "█" * filled + "·" * (width - filled)


def render(applications: list[Application], today: date, known_stack: set[str]) -> str:
    if not applications:
        return "No applications recorded yet. Add one with: jobtrack add --help"

    lines: list[str] = []
    add = lines.append

    add(f"JOB SEARCH REPORT — {today.isoformat()}")
    add("=" * 56)

    add("")
    add("VOLUME")
    for label, count in metrics.weekly_volume(applications, today):
        add(f"  {label}   {count:>3} applications")
    add(f"  total recorded: {len(applications)}")

    add("")
    add("FUNNEL")
    for name, rate in (
        ("answered", metrics.response_rate(applications)),
        ("interviewed", metrics.interview_rate(applications)),
        ("offers", metrics.offer_rate(applications)),
    ):
        add(f"  {name:<12} {_bar(rate)}  {rate}")
    delay = metrics.median_days_to_answer(applications)
    add(f"  median days to first answer: {delay if delay is not None else 'no answers yet'}")

    add("")
    add("RESPONSE RATE BY CHANNEL")
    for channel, rate in metrics.by_dimension(applications, lambda a: a.channel).items():
        add(f"  {channel:<18} {rate}")

    add("")
    add("RESPONSE RATE BY RESUME VARIANT")
    variants = metrics.by_dimension(applications, lambda a: a.resume or "unspecified")
    for variant, rate in sorted(variants.items(), key=lambda kv: -kv[1].value):
        add(f"  {variant:<28} {rate}")

    reasons = metrics.rejection_reasons(applications)
    if reasons:
        add("")
        add("WHY APPLICATIONS CLOSED")
        for reason, count in reasons.most_common():
            add(f"  {reason:<26} {count}")

    gaps = metrics.stack_gaps(applications, known_stack)
    if gaps:
        add("")
        add("MOST REQUESTED SKILLS I DO NOT HAVE")
        for skill, count in gaps.most_common(8):
            add(f"  {skill:<26} asked in {count} postings")

    stale = metrics.stale(applications, today)
    if stale:
        add("")
        add(f"STALE — no answer after 21 days ({len(stale)})")
        for app in stale[:10]:
            add(f"  {app.applied_on.isoformat()}  {app.company} — {app.role}")

    live = [a for a in applications if a.outcome is Outcome.PENDING and a.answered]
    if live:
        add("")
        add(f"LIVE CONVERSATIONS ({len(live)})")
        for app in sorted(live, key=lambda a: a.stage.rank, reverse=True):
            add(f"  [{app.stage.value:<9}] {app.company} — {app.role}")

    add("")
    add("WHAT THIS SUGGESTS")
    for line in _advice(applications, today, known_stack):
        add(f"  - {line}")

    return "\n".join(lines)


def _advice(applications: list[Application], today: date, known_stack: set[str]) -> list[str]:
    """Rules of thumb, stated as suggestions and never as certainties."""
    out: list[str] = []
    answered = metrics.response_rate(applications)
    recent = metrics.weekly_volume(applications, today, weeks=1)[0][1]

    if not answered.meaningful:
        out.append(
            f"only {answered.total} applications recorded — too few to conclude anything; "
            "keep the sample growing before changing strategy"
        )
    elif answered.value < 0.10:
        out.append(
            f"response rate is {answered} — the bottleneck is upstream of the interview: "
            "profile, targeting or proof of work, not how you interview"
        )

    if recent == 0:
        out.append("nothing sent in the last 7 days — the pipeline is empty by next month")

    gaps = metrics.stack_gaps(applications, known_stack)
    if gaps:
        top = ", ".join(skill for skill, _ in gaps.most_common(3))
        out.append(f"most repeated missing skills: {top} — learning one changes more postings than ten applications")

    stale_count = len(metrics.stale(applications, today))
    if stale_count >= 5:
        out.append(f"{stale_count} applications are past 21 days with no answer — treat them as closed")

    variants = metrics.by_dimension(applications, lambda a: a.resume or "unspecified")
    usable = {name: rate for name, rate in variants.items() if rate.total >= 3}
    if len(usable) >= 2:
        best = max(usable.items(), key=lambda kv: kv[1].value)
        worst = min(usable.items(), key=lambda kv: kv[1].value)
        if best[1].value > worst[1].value:
            out.append(f"resume '{best[0]}' is answering better than '{worst[0]}' so far")

    return out or ["nothing stands out this week; keep the volume steady"]
