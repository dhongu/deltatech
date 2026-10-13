# Confirmed bugs — 2026-10-03

## SALEPHONE-001 — P2: partner-phone change does not invalidate computed cache

Both sale.order and account.move partner_phone computations depend only on partner_id but read partner_id.phone. Read the field, update the same partner's phone in the same Environment, then read it again: no dependency trigger invalidates the cached old number. Add partner_id.phone or use an appropriate related field. Fresh requests may hide this defect; stored persistence is not claimed because these fields are nonstored.

Evidence: complete source, native fields.get_depends/models.modified invalidation contract previously traced, and account/sale view anchors checked. Source-only; database transaction/UI test not executed.

## Limits

Current field reflects partner phone rather than a document snapshot by implementation. No phone-format/business restriction inferred. No database/browser tests or source fixes.
