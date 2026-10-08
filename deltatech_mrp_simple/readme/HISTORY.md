## 20.0.1.1.3 (2026-10-08)

- Fixed SIMPLE-001: with several received products, each one was valued at the
  whole consumed cost, so the production was valued at a multiple of what was
  consumed. The consumed cost is now split once over the received products, in
  proportion to their standard value (standard price x quantity), or to their
  quantity when none has a standard price; the last line takes the rounding
  difference. A received line without quantity no longer causes a division by
  zero.
- Fixed SIMPLE-002: *Confirm* could be run again on a done simple production
  through RPC or a retried request, creating new consumption and receipt
  transfers and moving the stock a second time. A simple production can now be
  confirmed only once.

## 20.0.1.1.2 (2026-10-01)

- Migration to Odoo 20.0.

## 19.0.1.1.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
