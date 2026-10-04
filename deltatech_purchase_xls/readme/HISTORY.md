## 19.0.1.0.4 (2026-10-04)

- **Fix (PURCHASEXLS-002): importing order lines without an order in the
  context.** The import crashed before reading the file. The order is now
  taken from the order column (name, external id or database id, also when it
  is the first column) when all the rows point to the same order; otherwise
  the rows go to the standard import.
- **Fix (PURCHASEXLS-004): every row is checked when updating the lines of an
  order.** The row after a dropped row was not checked and could reach the
  standard import without an order. When several lines have the same product,
  the rows are matched in order to the first line not used yet; a row without
  a free line is dropped. A product cell that is not text (number, empty) no
  longer stops the import. The rows and columns passed by the caller are no
  longer changed.
- **Fix: clear messages in the Excel import wizard.** An empty or text
  quantity stops the import with the row number; with amounts, a row with
  quantity zero and a non-zero amount is reported, and a price that is not a
  number skips the row, as without amounts. An empty file (or a header only)
  is reported instead of failing with a technical error.
- **Fix: a new product created without a unit of measure gets the Units
  record** (`uom.product_uom_unit`) instead of the record with id 1.

## 19.0.1.0.3 (2026-10-04)

- Extend unit tests to cover the order lines action, the order line import (load) hooks, the import wizard (supplier and internal code search, amounts, units of measure, missing and new products, errors) and the export of vendor codes and names.

## 19.0.1.0.2 (2026-10-03)

- **Fix (PURCHASEXLS-001): supplier codes are matched on the order vendor
  and company.** The import took the first vendor pricing row with the code,
  whatever the vendor or the company, so a code used by two suppliers could
  add the wrong product to the order. The code is now looked up only on the
  pricing rows of the order vendor (or its company partner) for the order
  company or without company; a code that leads to several products (several
  rows, or a template with variants and no variant set) stops the import with
  a message instead of picking one. The internal code fallback is limited to
  products of the order company or shared ones, and the pricing row created
  for a new product gets the order company. Imports that relied on codes of
  other vendors no longer find those products.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
