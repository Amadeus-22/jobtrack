"""The model is the last line of defence against a log nobody can trust."""
from datetime import date

import pytest

from jobtrack.model import Application, Event, Outcome, Seniority, Stage


def make(**overrides) -> Application:
    base = dict(id="a1", company="Acme", role="Backend Engineer",
                applied_on=date(2026, 9, 1))
    return Application(**{**base, **overrides})


def test_stage_is_derived_from_the_furthest_event_not_the_last_one():
    app = make(events=(
        Event(date(2026, 9, 2), Stage.SCREENING),
        Event(date(2026, 9, 9), Stage.INTERVIEW),
        Event(date(2026, 9, 20), Stage.CLOSED),
    ))
    # CLOSED ranks last, so it is also the furthest: the pipeline ended there.
    assert app.stage is Stage.CLOSED


def test_an_application_with_no_events_sits_at_applied():
    assert make().stage is Stage.APPLIED
    assert make().answered is False


def test_answered_requires_someone_moving_it_past_applied():
    app = make(events=(Event(date(2026, 9, 3), Stage.SCREENING),))
    assert app.answered is True
    assert app.days_to_first_answer() == 2


def test_days_to_first_answer_is_none_while_nobody_replied():
    assert make().days_to_first_answer() is None


def test_events_out_of_order_are_rejected_at_construction():
    with pytest.raises(ValueError, match="chronological"):
        make(events=(
            Event(date(2026, 9, 10), Stage.SCREENING),
            Event(date(2026, 9, 2), Stage.INTERVIEW),
        ))


def test_required_fields_are_enforced():
    with pytest.raises(ValueError, match="id is required"):
        make(id="  ")
    with pytest.raises(ValueError, match="company and role"):
        make(company="")
    with pytest.raises(ValueError, match="asked_salary"):
        make(asked_salary=0)


def test_rejection_outcomes_are_recognisable_as_a_group():
    assert Outcome.REJECTED_STACK.is_rejection
    assert Outcome.REJECTED_EXPERIENCE.is_rejection
    assert not Outcome.NO_RESPONSE.is_rejection
    assert not Outcome.HIRED.is_rejection


def test_seniority_defaults_to_unspecified():
    assert make().seniority is Seniority.UNSPECIFIED
