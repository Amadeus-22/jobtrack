# Architecture

## Shape

Four layers, each depending only on the one below it:

```
cli.py        parses arguments, prints; contains no rules
  └── report.py     composes metrics into a page
        └── metrics.py    pure functions over a list of applications
              └── model.py     the domain, validated at construction
        └── store.py      reads and writes the log (only layer touching disk)
```

`metrics` and `report` never touch the filesystem and never call `date.today()`.
The current date arrives as an argument. That single rule is what makes the
tests deterministic and lets any report be regenerated for a past day.

## The domain

An `Application` is an immutable record plus an append-only tuple of `Event`s.
Stage is not stored; it is derived as the furthest stage any event reached. This
removes a whole class of bug — a record whose status says `interview` while its
events say otherwise — and it makes "days to first answer" computable, because
the first move past `applied` is always in the log with its date.

`Outcome` is a closed enumeration. Free-text reasons cannot be counted, and a
search that cannot count its rejections cannot tell a missing tool from a
missing year of experience.

## Storage

One JSON object per line, appended, in `data/applications.jsonl`, under version
control. The file is the database; `git log` is the audit trail.

Validation happens on read. A malformed line raises `StoreError` naming the line
number rather than being skipped, because a log that silently drops records
produces metrics that are wrong in the direction of optimism.

## Metrics

Every rate is a `Rate(hits, total)` rather than a float. The denominator travels
with the number, and `Rate.meaningful` marks samples below `MIN_SAMPLE` (8). The
report prints those as "small sample" instead of hiding them: an early search has
nothing but small samples, and pretending otherwise is how people rewrite a CV
that was working.

`stack_gaps` compares what postings asked for against `KNOWN_STACK` in `cli.py`.
That set is the one piece of the system that is deliberately subjective: it is
what its owner can defend in an interview, not what they have read about.

## Testing

27 tests, no mocks, no fixtures beyond `tmp_path`. The model and metrics are
pure, so they are tested directly; the store is tested against real files in a
temporary directory, including the failure paths — broken JSON, invalid dates,
missing fields, duplicate ids.

The tests that matter most are the boring ones: empty input never divides by
zero, a tiny sample is flagged rather than trusted, and a corrupt line is named
instead of ignored.
