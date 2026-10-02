## 19.0.1.0.2 (2026-10-02)

- Fix `stock.picking.categ_ids`: the compute had no `@api.depends`, so the categories stayed stale in the same transaction after the move lines changed. Tests check the computed categories.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
