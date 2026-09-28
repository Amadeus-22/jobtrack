# jobtrack

**Pipeline analytics for a job search — what you applied to, what answered, and what to do next.**

[![tests](https://img.shields.io/badge/tests-27%20passing-2ea44f?style=flat-square)](tests/)
[![python](https://img.shields.io/badge/python-3.11%2B-3776ab?style=flat-square&logo=python&logoColor=white)](pyproject.toml)
[![dependencies](https://img.shields.io/badge/runtime%20dependencies-none-6f42c1?style=flat-square)](docs/DECISIONS.md)
[![license](https://img.shields.io/badge/license-MIT-black?style=flat-square)](LICENSE)

---

## The problem

A job search produces exactly the kind of data people throw away: dozens of
applications, each with a stack, a channel, a salary figure and an outcome. Then
the next decision — rewrite the CV? learn Kubernetes? ask for more money? — gets
made from memory and mood.

After one week of applying, three questions were impossible to answer honestly:

| Question | Why it matters |
|---|---|
| Which résumé variant actually gets replies? | Rewriting the one that was working is the most common wasted week. |
| Which requirement keeps closing doors? | Missing years, missing tool and missing degree need three different responses. |
| Is the response rate low, or is the sample still too small to mean anything? | A rate over four applications reads 25% and sends you fixing the wrong thing. |

`jobtrack` answers all three from a log you keep in git.

---

## What it looks like

```
JOB SEARCH REPORT — 2026-09-28
========================================================

VOLUME
  2026-09-22..2026-09-28    12 applications
  total recorded: 12

FUNNEL
  answered     ····················  0.0% (0/12)
  interviewed  ····················  0.0% (0/12)
  offers       ····················  0.0% (0/12)
  median days to first answer: no answers yet

RESPONSE RATE BY RESUME VARIANT
  sustentacao-php              0.0% (0/1) (small sample)
  fullstack-ai                 0.0% (0/1) (small sample)

MOST REQUESTED SKILLS I DO NOT HAVE
  AWS                        asked in 4 postings
  PySpark                    asked in 2 postings
  RAG                        asked in 2 postings
  LangChain                  asked in 2 postings

WHAT THIS SUGGESTS
  - response rate is 0.0% (0/12) — the bottleneck is upstream of the interview:
    profile, targeting or proof of work, not how you interview
  - most repeated missing skills: AWS, PySpark, RAG — learning one changes more
    postings than ten applications
```

---

## Quick start

```bash
git clone https://github.com/Amadeus-22/jobtrack.git
cd jobtrack
python -m pytest -q          # 27 tests, no runtime dependencies
make report                  # the weekly page
```

**Record an application**

```bash
python -m jobtrack add \
  --id 2026-10-02-acme \
  --company "Acme" --role "Backend Engineer" \
  --channel linkedin --seniority mid \
  --stack Python Go PostgreSQL Docker \
  --resume backend-python --salary 12000 --currency BRL
```

**Record what happened to it**

```bash
python -m jobtrack event --id 2026-10-02-acme --stage screening --note "recruiter call"
python -m jobtrack event --id 2026-10-02-acme --stage closed --outcome rejected_experience
```

**Commands**

| Command | Does |
|---|---|
| `add` | Record a new application |
| `event` | Append a stage change, optionally closing it with a reason |
| `stats` | Headline numbers only |
| `report` | The weekly page |
| `validate` | Check every record in the log |

Every command accepts `--date 2026-09-28`, which computes the report as of that
day. Reports are reproducible: the same log and the same date always produce the
same page.

---

## What it measures

- **Volume per week** — an empty pipeline is visible before it becomes an empty month.
- **Funnel** — answered, interviewed, offers, each with its denominator.
- **Response rate by channel and by résumé variant** — the only way to tell whether a rewrite helped.
- **Why applications closed** — from a closed vocabulary: experience, stack, education, compensation, other.
- **Most requested skills you do not have** — the list that decides what to learn next.
- **Stale applications** — past 21 days with no answer, so they stop being counted as hope.

---

## Design

Four layers, each depending only on the one below it:

```
cli.py        parses arguments and prints; contains no rules
  └── report.py     composes metrics into a page
        └── metrics.py    pure functions over a list of applications
              └── model.py     the domain, validated at construction
        └── store.py      the only layer that touches disk
```

Three decisions shape everything else:

**Stage is derived, never stored.** An application is an immutable record plus an
append-only list of events, and its stage is the furthest stage any event
reached. A record whose status contradicts its own history cannot exist.

**Rates carry their denominator.** `Rate(hits, total)` instead of a float, with
samples under eight flagged as *small sample* in the report. The most expensive
mistake in a job search is acting on a number computed over four applications.

**`today` is always a parameter.** Nothing below the CLI calls `date.today()`, so
tests are deterministic and any past week can be recomputed exactly.

Full reasoning in [docs/DECISIONS.md](docs/DECISIONS.md); the layer map and
testing strategy in [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md); what comes next
in [docs/ROADMAP.md](docs/ROADMAP.md).

---

## Storage

One JSON object per line in `data/applications.jsonl`, under version control.
The file is the database and `git log` is the audit trail. A malformed line
raises an error naming its line number instead of being skipped, because a log
that silently drops records produces metrics that are wrong in the direction of
optimism.

```json
{"id":"2026-09-26-arturia-n3","company":"Arturia Sales Tech","role":"Analista de Sustentação N3 - PHP","applied_on":"2026-09-26","channel":"linkedin","seniority":"mid","stack":["PHP","Linux","SQL","REST"],"resume":"sustentacao-php","asked_salary":10000,"currency":"BRL"}
```

Each `resume` value points to a document in the résumé dataset,
[`data/resumes/`](data/resumes/): one PDF and its HTML source per variant, plus a
`manifest.jsonl` with role, language, date and checksum.

---

## Layout

```
src/jobtrack/
  model.py     Application, Event, Stage, Outcome — validated at construction
  store.py     JSON Lines log: load, append, rewrite; fails loudly with line numbers
  metrics.py   pure functions: rates, medians, groupings, skill gaps
  report.py    renders the weekly page
  cli.py       argument parsing only
tests/         27 tests across the model, the store and every metric
docs/          architecture, decisions, roadmap
data/          the log itself, plus the résumé dataset in data/resumes/
```

---

## Tests

```bash
python -m pytest -q
27 passed
```

No mocks and no fixtures beyond `tmp_path`. The model and metrics are pure and
tested directly; the store is tested against real files, including the failure
paths — broken JSON, invalid dates, missing fields, duplicate ids.

The tests that matter most are the unglamorous ones: empty input never divides
by zero, a tiny sample is flagged rather than trusted, and a corrupt line is
named instead of ignored.

---

## License

MIT — see [LICENSE](LICENSE).
