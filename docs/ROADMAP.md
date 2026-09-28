# Roadmap

Sequential. Each phase ends with something usable on its own; nothing starts
before the previous phase has been in real use for at least a week.

## Phase 1 — The log (done)

Domain model, JSON Lines store, metrics, weekly report, CLI, 27 tests.

**Done when:** a week of real applications is recorded and the report is read on
a Monday without being rewritten to make sense.

## Phase 2 — Follow-ups

- `jobtrack followup` — applications worth a nudge: answered once, then silent
  for more than seven days.
- A reminder window per application, so a promised "we'll get back to you in two
  weeks" is tracked instead of remembered.

**Done when:** a follow-up is sent because the tool surfaced it, not because it
came to mind in the shower.

## Phase 3 — Résumé attribution

- Link each application to the résumé file that was sent, by content hash, so
  "variant X answers better" survives the variant being edited.
- Report the comparison only once each variant has enough applications to matter.

**Done when:** a résumé decision is made on the comparison rather than on taste.

## Phase 4 — Compensation

- Track offered ranges against asked ranges.
- Report where asking more stopped producing answers — the only empirical way to
  find the ceiling of a market from inside it.

**Done when:** the next salary figure is chosen from the data in this repository.

## Explicitly out of scope

- Scraping job boards. The bottleneck is never finding postings.
- Auto-applying. Volume without targeting is what the metrics exist to prevent.
- A web interface. A terminal page read once a week is the right size for this.
