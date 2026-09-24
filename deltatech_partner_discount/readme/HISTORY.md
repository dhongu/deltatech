## 19.0.1.0.1 (2026-09-24)

- Port pe Odoo 19: `_()` înlocuit cu `self.env._()`, convenția Odoo 19
  (pylint-odoo `prefer-env-translation`). Restul codului e neschimbat —
  niciun API folosit (`fields.Float`, `api.onchange`, `api.model_create_multi`,
  `has_group`) nu s-a modificat pe O19.
