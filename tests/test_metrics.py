"""Metrics must stay honest when the sample is tiny — that is when they mislead."""
from datetime import date

from jobtrack.metrics import (
    MIN_SAMPLE, by_dimension, interview_rate, median_days_to_answer, offer_rate,
    rejection_reasons, response_rate, salary_asked, stack_gaps, stale, weekly_volume,
)
from jobtrack.model import Application, Event, Outcome, Stage

TODAY = date(2026, 9, 28)


def app(id_: str, applied: date, *, events=(), outcome=Outcome.PENDING,
        channel="linkedin", resume="", stack=(), salary=None, currency="BRL") -> Application:
    return Application(id=id_, company=f"Co{id_}", role="Engineer", applied_on=applied,
                       channel=channel, resume=resume, stack=tuple(stack),
                       asked_salary=salary, currency=currency,
                       events=tuple(events), outcome=outcome)


def test_response_rate_counts_only_applications_that_moved():
    data = [
        app("1", date(2026, 9, 1), events=[Event(date(2026, 9, 4), Stage.SCREENING)]),
        app("2", date(2026, 9, 1)),
        app("3", date(2026, 9, 1)),
    ]
    rate = response_rate(data)
    assert (rate.hits, rate.total) == (1, 3)
    assert rate.percent == 33.3


def test_a_rate_below_the_minimum_sample_is_flagged_not_hidden():
    small = response_rate([app(str(i), date(2026, 9, 1)) for i in range(MIN_SAMPLE - 1)])
    assert small.meaningful is False
    assert "small sample" in str(small)

    enough = response_rate([app(str(i), date(2026, 9, 1)) for i in range(MIN_SAMPLE)])
    assert enough.meaningful is True
    assert "small sample" not in str(enough)


def test_empty_input_never_divides_by_zero():
    assert response_rate([]).value == 0.0
    assert interview_rate([]).percent == 0.0
    assert offer_rate([]).total == 0
    assert median_days_to_answer([]) is None


def test_interview_rate_ignores_applications_stuck_in_screening():
    data = [
        app("1", date(2026, 9, 1), events=[Event(date(2026, 9, 2), Stage.SCREENING)]),
        app("2", date(2026, 9, 1), events=[Event(date(2026, 9, 5), Stage.INTERVIEW)]),
    ]
    assert interview_rate(data).hits == 1


def test_median_days_to_answer_uses_only_applications_that_answered():
    data = [
        app("1", date(2026, 9, 1), events=[Event(date(2026, 9, 3), Stage.SCREENING)]),
        app("2", date(2026, 9, 1), events=[Event(date(2026, 9, 11), Stage.SCREENING)]),
        app("3", date(2026, 9, 1)),
    ]
    assert median_days_to_answer(data) == 6


def test_by_dimension_groups_and_keeps_each_denominator():
    data = [
        app("1", date(2026, 9, 1), channel="upwork",
            events=[Event(date(2026, 9, 2), Stage.SCREENING)]),
        app("2", date(2026, 9, 1), channel="upwork"),
        app("3", date(2026, 9, 1), channel="referral",
            events=[Event(date(2026, 9, 2), Stage.INTERVIEW)]),
    ]
    grouped = by_dimension(data, lambda a: a.channel)
    assert grouped["upwork"].hits == 1 and grouped["upwork"].total == 2
    assert grouped["referral"].percent == 100.0


def test_rejection_reasons_counts_only_real_rejections():
    data = [
        app("1", date(2026, 9, 1), outcome=Outcome.REJECTED_STACK),
        app("2", date(2026, 9, 1), outcome=Outcome.REJECTED_STACK),
        app("3", date(2026, 9, 1), outcome=Outcome.REJECTED_EXPERIENCE),
        app("4", date(2026, 9, 1), outcome=Outcome.NO_RESPONSE),
    ]
    counted = rejection_reasons(data)
    assert counted["rejected_stack"] == 2
    assert counted["rejected_experience"] == 1
    assert "no_response" not in counted


def test_stack_gaps_are_case_insensitive_and_exclude_what_i_know():
    data = [
        app("1", date(2026, 9, 1), stack=["Python", "Kubernetes"]),
        app("2", date(2026, 9, 1), stack=["kubernetes", "Terraform"]),
    ]
    gaps = stack_gaps(data, known={"python"})
    assert gaps["Kubernetes"] == 1 and gaps["kubernetes"] == 1
    assert "Python" not in gaps
    assert gaps["Terraform"] == 1


def test_stale_ignores_anything_that_already_answered_or_closed():
    data = [
        app("old-silent", date(2026, 9, 1)),
        app("old-answered", date(2026, 9, 1),
            events=[Event(date(2026, 9, 3), Stage.SCREENING)]),
        app("old-closed", date(2026, 9, 1), outcome=Outcome.REJECTED_STACK),
        app("recent", date(2026, 9, 25)),
    ]
    assert [a.id for a in stale(data, TODAY)] == ["old-silent"]


def test_weekly_volume_returns_the_requested_windows_in_order():
    data = [app("1", date(2026, 9, 28)), app("2", date(2026, 9, 27)),
            app("3", date(2026, 9, 10))]
    weeks = weekly_volume(data, TODAY, weeks=2)
    assert len(weeks) == 2
    assert weeks[-1][1] == 2


def test_salary_asked_separates_currencies():
    data = [
        app("1", date(2026, 9, 1), salary=12000, currency="BRL"),
        app("2", date(2026, 9, 1), salary=9000, currency="BRL"),
        app("3", date(2026, 9, 1), salary=3000, currency="USD"),
    ]
    assert salary_asked(data, "BRL") == (9000, 12000, 10500)
    assert salary_asked(data, "USD") == (3000, 3000, 3000)
    assert salary_asked(data, "EUR") is None
