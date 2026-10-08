# Confirmed bugs — 2026-10-03

## MRPBOM-001 — P1: derived recipes lose base yield and other recipe data

**Status:** Fixed in 19.0.1.0.7. `recompute_from_base()` copies the base
`product_qty` / `product_uom_id`, operations (with dependencies), components and
by-products, skipping entries restricted to other variants. Covered by
`test_derived_bom_keeps_base_recipe` (base 10 units from 20 components, MO for
10 consumes 20).

`models/mrp_production.py:28–35` and `report/mrp_report_bom_structure.py:20–27` create a derived BoM with only template/variant/type/code. `models/mrp_bom.py:41–64` copies component lines but never the base product_qty or product_uom_id. Native BoM product_qty defaults to1; native production raw-move generation uses converted MO quantity / BoM product_qty as its factor (`mrp_production.py:1344`). A base yielding10 units from20 components becomes a derived yielding1 from20, so an MO for10 consumes200 instead of20. Base operations and byproducts are also omitted. Preserve the base header and required recipe relations when deriving, with variant substitution applied afterward.

Evidence: complete derived-create/recompute source traced through native default/yield factor and report creation path. Arithmetic follows the exact native factor. No database derived-BoM/MO/report reproduction executed; copying operation-linked component lines without copied operations needs additional validation.

## Limits

Entire module source read, report helper signatures match native Odoo19. Base/derived searches omit explicit company scoping and report/onchange paths mutate persisted shared recipes; their effects on multi-company choice and existing MO references remain integration validation limits rather than separately reproduced findings. Attribute replacement and template matching reviewed without a variant database scenario.
