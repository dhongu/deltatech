## 20.0.2.0.0 (2026-10-03)

- The module becomes an extension of the standard `receipt_status`: the own
  `picking_status` field (computed, not stored, searched in Python on every
  order) is removed.
- Filters by receipt status, list column shown by default, tracking in the
  chatter.
- Migration: saved filters (`ir.filters`) and export templates on
  `picking_status` are rewritten on `receipt_status`; views edited in the
  database that still use the old field are reported in the log.
