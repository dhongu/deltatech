## 19.0.1.1.4 (2026-10-12)

- Fixed SIMPLE-003: the received products were valued at their current product
  cost, not at the cost allocated from the consumed components, so the
  difference went silently into the stock value and the average cost. The
  receipt moves of a simple production are now valued at the allocated unit
  price. The module now depends on `stock_account`.
- Two received lines with the same product and unit are merged into one move at
  their weighted average price, instead of the price of the first line.

## 19.0.1.1.3 (2026-10-08)

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
- The *Compute price* button is hidden after confirmation (the view attribute
  was misspelled).

## 19.0.1.1.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
