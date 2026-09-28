# jobtrack

Pipeline analytics for a job search: what you applied to, what answered, and what
to do next week.

A job search generates exactly the kind of data people throw away — dozens of
applications, each with a stack, a channel, a salary figure and an outcome — and
then it gets decided by memory and mood. `jobtrack` keeps the log, computes the
few rates that change behaviour, and prints a page you can act on.

It has no dependencies. The log is a text file under version control.

## Why it exists

After a week of applying, three questions were impossible to answer honestly:

- Which résumé variant actually gets replies?
- Which requirement keeps closing doors — years of experience, a missing tool,
  or an unfinished degree?
- Is the response rate low because of the applications, or because the sample is
  still too small to mean anything?

The third question is the reason the codebase is stricter than it looks. A rate
computed over four applications will happily read 25% and send someone
rewriting a CV that was never the problem. Every rate here carries its
denominator and is flagged when the sample is too small to support a decision.

## Install and use

```bash
python -m pytest -q            # 27 tests, no dependencies beyond pytest
make report                    # the weekly page
make stats                     # headline numbers only
```

Record an application:

```bash
python -m jobtrack add \
  --id 2026-10-02-acme \
  --company "Acme" --role "Backend Engineer" \
  --channel linkedin --seniority mid \
  --stack Python Go PostgreSQL Docker \
  --resume backend-python --salary 12000 --currency BRL
```

Record what happened to it:

```bash
python -m jobtrack event --id 2026-10-02-acme --stage screening --note "recruiter call"
python -m jobtrack event --id 2026-10-02-acme --stage closed --outcome rejected_experience
```

Reports are reproducible: `--date 2026-09-28` computes everything as of that day,
so a report can be regenerated later and still say the same thing.

## What it reports

- Volume per week, so an empty pipeline is visible before it becomes an empty month.
- Funnel: answered, interviewed, offers — each with its denominator.
- Response rate by channel and by résumé variant, which is the only way to tell
  whether a rewrite helped.
- Why applications closed, from a closed vocabulary of reasons.
- Most requested skills absent from `KNOWN_STACK` — the list that decides what to
  learn next.
- Applications past 21 days with no answer, so they stop being counted as hope.

## Layout

```
src/jobtrack/
  model.py     domain: Application, Event, Stage, Outcome — validated at construction
  store.py     JSON Lines log: load, append, rewrite; fails loudly with line numbers
  metrics.py   pure functions: rates, medians, groupings, gaps
  report.py    renders the weekly page from metrics
  cli.py       argument parsing only; no logic lives here
tests/         27 tests covering the model, the store and every metric
docs/          architecture, decisions, roadmap
data/          the log itself
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for how the pieces fit and
[docs/DECISIONS.md](docs/DECISIONS.md) for why they are shaped this way.
