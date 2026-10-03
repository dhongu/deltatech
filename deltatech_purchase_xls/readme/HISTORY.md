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
