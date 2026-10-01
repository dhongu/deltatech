## 19.0.2.0.11 (2026-10-01)

- **Serialized stock is no longer blocked when Check Serial No. is off.** On a
  location with the serial check disabled, the no-negative-stock check cleared
  the line's serial number and then searched explicitly for quants *without* a
  serial, so it excluded the very quants holding the stock and blocked a
  legitimate transfer, although reservation had gone through. The lot filter is
  now left out entirely in that case: the physical quantity is summed across all
  serial numbers of the location (product, package and owner filters kept), and
  every line of the product consumes from that same aggregate. With the serial
  check on (the default), the check stays per serial number. (STOCK-001)

## 19.0.2.0.10 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.2.0.9 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.

## 19.0.2.0.8 (2026-09-22)

- **Several lines of one validation no longer share the same stock.** The check
  runs over the whole recordset before `super()._action_done()` writes anything
  to the quants, so every line used to read the same untouched quantity. Taken
  one by one, two lines of 1 against a stock of 1 are each legal, and the
  transfer still landed at -1. It now carries what the earlier lines of the same
  batch already took from each quant, keyed by product, location, lot, package
  and owner -- so lines on different quants still do not add up.
  Reported twice from the shop floor: 2 pieces picked to shelve when only 1 was
  on hand.
