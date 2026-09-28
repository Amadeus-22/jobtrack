"""A log that loses or corrupts a record silently is worse than no log."""
from datetime import date

import pytest

from jobtrack.model import Application, Event, Outcome, Stage
from jobtrack.store import StoreError, append, load, save_all


def sample(id_="a1") -> Application:
    return Application(id=id_, company="Acme", role="Backend Engineer",
                       applied_on=date(2026, 9, 1), channel="linkedin",
                       stack=("Python", "Go"), resume="backend", asked_salary=12000)


def test_round_trip_preserves_every_field(tmp_path):
    path = tmp_path / "apps.jsonl"
    original = sample()
    append(original, path)
    loaded = load(path)[0]
    assert loaded == original


def test_events_and_outcome_survive_a_rewrite(tmp_path):
    path = tmp_path / "apps.jsonl"
    app = sample()
    append(app, path)
    updated = Application(
        id=app.id, company=app.company, role=app.role, applied_on=app.applied_on,
        channel=app.channel, stack=app.stack, resume=app.resume,
        asked_salary=app.asked_salary,
        events=(Event(date(2026, 9, 5), Stage.INTERVIEW, "call"),),
        outcome=Outcome.REJECTED_STACK,
    )
    save_all([updated], path)
    loaded = load(path)[0]
    assert loaded.events[0].stage is Stage.INTERVIEW
    assert loaded.events[0].note == "call"
    assert loaded.outcome is Outcome.REJECTED_STACK


def test_missing_file_reads_as_empty_not_as_an_error(tmp_path):
    assert load(tmp_path / "nothing.jsonl") == []


def test_duplicate_ids_are_refused_on_append(tmp_path):
    path = tmp_path / "apps.jsonl"
    append(sample(), path)
    with pytest.raises(StoreError, match="already exists"):
        append(sample(), path)


def test_a_broken_line_names_its_line_number(tmp_path):
    path = tmp_path / "apps.jsonl"
    append(sample("a1"), path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("{not json}\n")
    with pytest.raises(StoreError, match="line 2"):
        load(path)


def test_an_invalid_date_is_reported_instead_of_silently_dropped(tmp_path):
    path = tmp_path / "apps.jsonl"
    path.write_text('{"id":"x","company":"A","role":"R","applied_on":"31/09/2026"}\n',
                    encoding="utf-8")
    with pytest.raises(StoreError, match="not an ISO date"):
        load(path)


def test_a_missing_required_field_is_named(tmp_path):
    path = tmp_path / "apps.jsonl"
    path.write_text('{"id":"x","company":"A"}\n', encoding="utf-8")
    with pytest.raises(StoreError, match="missing required field 'role'"):
        load(path)


def test_comments_and_blank_lines_are_ignored(tmp_path):
    path = tmp_path / "apps.jsonl"
    append(sample(), path)
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n// a note to myself\n")
    assert len(load(path)) == 1
