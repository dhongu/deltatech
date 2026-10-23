## 19.0.1.0.5 (2026-10-23)

- Fix: exploding an empty bill of materials no longer fails with "Expected singleton:
  mrp.bom()". The native manufacturing order form does this while computing the work
  orders of an order without a bill, so opening a new manufacturing order crashed as
  soon as the module was installed.

## 19.0.1.0.4 (2026-10-22)

- Listed on Odoo Apps as *BoM Quantity Formulas* (was *MRP BoM Formula*). The technical name `deltatech_mrp_bom_formula` does not change.

## 19.0.1.0.3 (2026-10-17)

- Fixed BOMFORMULA-001: a quantity formula on a nested kit bill of material
  was ignored when no line of the root bill had a formula. Component
  quantities now follow the formulas at every kit level.

## 19.0.1.0.2 (2026-10-10)

- Usage guide (`USAGE.md`) rebuilt from the consultant sheet, with numbered steps and screenshots; new `CONFIGURE.md`.

## 19.0.1.0.1 (2026-09-30)

- New module icon in the flat style of the other modules; it replaces the old one.
