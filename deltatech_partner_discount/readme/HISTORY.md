## 19.0.1.0.1 (2026-09-24)

- Port pe Odoo 19: `_()` înlocuit cu `self.env._()`, convenția Odoo 19
  (pylint-odoo `prefer-env-translation`). Restul codului e neschimbat —
  niciun API folosit (`fields.Float`, `api.onchange`, `api.model_create_multi`,
  `has_group`) nu s-a modificat pe O19.
- Fix: `security/groups.xml` seta `category_id` pe `res.groups`, câmp
  eliminat pe Odoo 19 (`ValueError: Invalid field 'category_id' in
  'res.groups'` la încărcarea registry-ului, prins de testele CI). Scos.
