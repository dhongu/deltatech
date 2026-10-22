## 20.0.1.1.0 (2026-10-22)

- The product manufacturer field is renamed from `manufacturer` to `manufacturer_id`, also in Invoice Analysis. The migration keeps the values and the exports; saved filters and custom views are updated too where `odoo.upgrade.util` is available (as on odoo.sh). Server actions and external integrations that use the old name must be updated by hand. A database coming from 19.0 with the field already renamed (19.0.1.1.0) is left as it is.
- Invoice Analysis: search by manufacturer and "Group By > Manufacturer".

## 20.0.1.0.2 (2026-10-09)

- Apps Store banner (banner.json).

## 20.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
