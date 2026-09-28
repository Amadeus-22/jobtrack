# Decisions

Each entry records what was chosen, what it cost, and what would reverse it.

## D1 — No runtime dependencies

**Chosen:** standard library only; `pytest` for development.

**Why:** the tool has to run on any machine, including a borrowed one, years
from now. Every dependency is a future failure that has nothing to do with the
problem being solved.

**Cost:** no YAML, no rich tables, argument parsing by hand.

**Reversed if:** the report grows into something a terminal cannot express — a
chart, an export — at which point a dependency buys more than it costs.

## D2 — JSON Lines instead of SQLite

**Chosen:** one JSON object per line, in git.

**Why:** the history of the search is as interesting as its current state, and
`git log` gives that for free. A single record can be corrected in any editor.
Diffs are readable in a pull request.

**Cost:** no queries, no indexes, and a full rewrite whenever a record changes.
At the scale of a job search — hundreds of records, not millions — that is free.

**Reversed if:** the log passes tens of thousands of records or two processes
need to write at once.

## D3 — Stage is derived, never stored

**Chosen:** `Application.stage` is computed from the event list.

**Why:** stored status drifts from its history. Derived status cannot.

**Cost:** appending an event is the only way to move an application, which is
slightly more typing than setting a field.

**Reversed if:** nothing foreseeable; this is the cheapest correctness guarantee
in the codebase.

## D4 — Rates carry their denominator

**Chosen:** `Rate(hits, total)` instead of a float, with `MIN_SAMPLE = 8`.

**Why:** the most expensive mistake in a job search is acting on a rate computed
over four applications. The type makes the sample size impossible to drop, and
the report says "small sample" out loud.

**Cost:** slightly more verbose call sites.

**Reversed if:** never — this is the whole reason the tool exists rather than a
spreadsheet.

## D5 — Rejection reasons are a closed vocabulary

**Chosen:** an `Outcome` enum with five explicit rejection reasons.

**Why:** "they said no" cannot be counted. "Rejected for years of experience,
seven times" changes what you apply to next week.

**Cost:** some rejections do not fit and land in `rejected_other`. A reason that
keeps landing there is a signal the vocabulary needs a new member — a deliberate,
visible change rather than free text nobody aggregates.

## D6 — `today` is always a parameter

**Chosen:** no function calls `date.today()` except the CLI.

**Why:** deterministic tests, and reports that can be regenerated for any past
date and still produce the same page.

**Cost:** one extra argument threaded through the call chain.
