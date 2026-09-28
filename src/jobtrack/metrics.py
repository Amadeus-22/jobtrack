"""The numbers worth acting on.

Every function here is pure: applications in, numbers out, no I/O and no clock
of its own. `today` is always a parameter, so a report can be recomputed for any
date and a test never depends on when it runs.

Rates are reported alongside their denominator. A 100% response rate over one
application is noise wearing a suit, and the report has to be able to say so.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from statistics import median

from .model import Application, Outcome, Stage

# Below this many applications, a rate is reported but flagged as not yet meaningful.
MIN_SAMPLE = 8


@dataclass(frozen=True, slots=True)
class Rate:
    """A ratio that knows how much evidence stands behind it."""

    hits: int
    total: int

    @property
    def value(self) -> float:
        return self.hits / self.total if self.total else 0.0

    @property
    def percent(self) -> float:
        return round(100 * self.value, 1)

    @property
    def meaningful(self) -> bool:
        return self.total >= MIN_SAMPLE

    def __str__(self) -> str:
        mark = "" if self.meaningful else " (small sample)"
        return f"{self.percent}% ({self.hits}/{self.total}){mark}"


def response_rate(applications: list[Application]) -> Rate:
    """Share of applications that ever got a human reply."""
    return Rate(sum(1 for a in applications if a.answered), len(applications))


def interview_rate(applications: list[Application]) -> Rate:
    """Share that reached an interview or further."""
    hits = sum(1 for a in applications if a.stage.rank >= Stage.INTERVIEW.rank)
    return Rate(hits, len(applications))


def offer_rate(applications: list[Application]) -> Rate:
    return Rate(sum(1 for a in applications if a.outcome is Outcome.HIRED), len(applications))


def median_days_to_answer(applications: list[Application]) -> float | None:
    """Median calendar days until the first reply, among those that replied."""
    delays = [d for a in applications if (d := a.days_to_first_answer()) is not None]
    return median(delays) if delays else None


def by_dimension(applications: list[Application], key) -> dict[str, Rate]:
    """Response rate grouped by any attribute: channel, seniority, resume."""
    buckets: dict[str, list[Application]] = defaultdict(list)
    for app in applications:
        buckets[str(key(app))].append(app)
    return {name: response_rate(group) for name, group in sorted(buckets.items())}


def rejection_reasons(applications: list[Application]) -> Counter[str]:
    """What actually closes doors, counted."""
    return Counter(
        a.outcome.value for a in applications if a.outcome.is_rejection
    )


def stack_gaps(applications: list[Application], known: set[str]) -> Counter[str]:
    """Technologies asked for across postings that are not in `known`.

    This is the list that decides what to learn next: not what feels exciting,
    but what keeps appearing between you and the roles you want.
    """
    wanted: Counter[str] = Counter()
    lowered = {k.lower() for k in known}
    for app in applications:
        for item in app.stack:
            if item.lower() not in lowered:
                wanted[item] += 1
    return wanted


def stale(applications: list[Application], today: date, after_days: int = 21) -> list[Application]:
    """Applications old enough to be treated as closed, so they stop being hope."""
    return [
        a
        for a in applications
        if a.outcome is Outcome.PENDING
        and not a.answered
        and a.age_in_days(today) >= after_days
    ]


def weekly_volume(applications: list[Application], today: date, weeks: int = 4) -> list[tuple[str, int]]:
    """Applications sent per week, most recent week last."""
    counts: list[tuple[str, int]] = []
    for index in range(weeks - 1, -1, -1):
        end = today - timedelta(days=7 * index)
        start = end - timedelta(days=6)
        label = f"{start.isoformat()}..{end.isoformat()}"
        counts.append((label, sum(1 for a in applications if start <= a.applied_on <= end)))
    return counts


def salary_asked(applications: list[Application], currency: str) -> tuple[int, int, float] | None:
    """Minimum, maximum and median of what you asked for, in one currency."""
    values = [a.asked_salary for a in applications
              if a.asked_salary is not None and a.currency == currency]
    if not values:
        return None
    return min(values), max(values), median(values)
