## Part of the Terrabit POS Ecosystem

This module is a small standalone addition to standard `point_of_sale`. It is designed to work
alongside the rest of the Terrabit POS suite and the official Romanian fiscal compliance modules,
without any overlap:

- **deltatech_pos** / **deltatech_pos_base** — print fiscal receipts and drive cash management on a certified cash register
- **deltatech_ecr_connect** — shared fiscal document model, ECR format converter and Terrabit Connect sender
- **deltatech_pos_price_sync** — pushes live product price changes to already open POS sessions, using the same live-bus channel as this module
- **deltatech_pos_fix** — corrects POS total calculation for tax-included fiscal position mapping
- **l10n_ro_pos_fiscal_compliance** — AMEF fiscal receipt tracking, Z report reconciliation and session blocking
- **l10n_ro_anaf_d394_pos** — reports POS fiscal receipts in the D394 (op. 2) declaration to ANAF
- **l10n_ro_pos_returns** — dedicated return invoice and cash register line for every POS return
