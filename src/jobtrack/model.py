"""The domain: an application, the events that happen to it, and why it ended.

Two rules drive the design.

First, an application is an immutable record plus an append-only list of events.
Status is never edited in place; it is derived from the last event. A pipeline
where you can silently rewrite history cannot answer "how long did they take to
reply", which is one of the few numbers that actually changes behaviour.

Second, a rejection without a reason is a lost lesson. `Outcome` forces the
reason into a small, closed vocabulary, because free text cannot be counted and
"they didn't like me" is not a category you can act on.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum


class Stage(str, Enum):
    """Where an application currently sits. Ordered from first to last."""

    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    TECHNICAL = "technical"
    OFFER = "offer"
    CLOSED = "closed"

    @property
    def rank(self) -> int:
        return list(Stage).index(self)


class Outcome(str, Enum):
    """Why an application ended. A closed vocabulary, on purpose."""

    PENDING = "pending"
    NO_RESPONSE = "no_response"
    REJECTED_EXPERIENCE = "rejected_experience"    # years required
    REJECTED_STACK = "rejected_stack"              # a tool or language I lack
    REJECTED_EDUCATION = "rejected_education"      # degree not completed
    REJECTED_COMPENSATION = "rejected_compensation"
    REJECTED_OTHER = "rejected_other"
    WITHDREW = "withdrew"
    HIRED = "hired"

    @property
    def is_rejection(self) -> bool:
        return self.name.startswith("REJECTED")


class Seniority(str, Enum):
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    UNSPECIFIED = "unspecified"


@dataclass(frozen=True, slots=True)
class Event:
    """One dated thing that happened to an application."""

    on: date
    stage: Stage
    note: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.on, date):
            raise ValueError("event date must be a date")
        if not isinstance(self.stage, Stage):
            raise ValueError("event stage must be a Stage")


@dataclass(frozen=True, slots=True)
class Application:
    """One application, with everything needed to learn from it later."""

    id: str
    company: str
    role: str
    applied_on: date
    channel: str = "unknown"           # linkedin, upwork, company site, referral
    seniority: Seniority = Seniority.UNSPECIFIED
    stack: tuple[str, ...] = ()        # what the posting asked for
    resume: str = ""                   # which CV variant was sent
    asked_salary: int | None = None     # in the currency below
    currency: str = "BRL"
    remote: bool = True
    events: tuple[Event, ...] = ()
    outcome: Outcome = Outcome.PENDING
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.id or not self.id.strip():
            raise ValueError("application id is required")
        if not self.company.strip() or not self.role.strip():
            raise ValueError("company and role are required")
        if not isinstance(self.applied_on, date):
            raise ValueError("applied_on must be a date")
        if self.asked_salary is not None and self.asked_salary <= 0:
            raise ValueError("asked_salary must be positive when present")
        previous: date | None = None
        for event in self.events:
            if previous is not None and event.on < previous:
                raise ValueError("events must be in chronological order")
            previous = event.on

    @property
    def stage(self) -> Stage:
        """Derived, never stored: the furthest stage reached."""
        if not self.events:
            return Stage.APPLIED
        return max((e.stage for e in self.events), key=lambda s: s.rank)

    @property
    def answered(self) -> bool:
        """Did a human on the other side ever move this forward?"""
        return any(e.stage.rank > Stage.APPLIED.rank for e in self.events)

    def days_to_first_answer(self) -> int | None:
        """Calendar days from applying to the first sign of life, if any."""
        for event in self.events:
            if event.stage.rank > Stage.APPLIED.rank:
                return (event.on - self.applied_on).days
        return None

    def age_in_days(self, today: date) -> int:
        return (today - self.applied_on).days
