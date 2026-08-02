# Changelog

## 19.0.0.0.6 (2026-07-31)

- Fix: analytic lines generated from `out_receipt` (Sales Receipt) invoices
  kept `team_id` empty on `account.analytic.line`, even though
  `analytic_distribution` on the source `account.move.line` was already
  correct (fixed in 19.0.0.0.5). `AccountAnalyticLine.create()` copies
  `team_id` from `move_id.team_id` only for `out_invoice`/`out_refund` —
  `out_receipt` was missing from that list, unlike the equivalent list in
  `account_move.py`. Added `out_receipt` so both stay consistent.

## 19.0.0.0.5 (2026-07-27)

- Fix: `_compute_analytic_distribution` looked up the distribution model by
  `move_id.team_id` but never declared it as a dependency, so lines kept
  their stale (often empty) analytic distribution whenever the sales team
  changed on an existing invoice, instead of only at creation time.
- Fix: `out_receipt` (Sales Receipt) invoices were excluded from the
  team-based analytic matching, so their revenue lines never got an
  analytic account, unlike `out_invoice`/`out_refund` lines.
