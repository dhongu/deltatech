## 20.0.1.0.1 (2026-10-02)

- Migration to Odoo 20.0. The standard wizard now selects the vendor through
  `partner_id` (`res.partner`), forwarded as `procurement_partner`; the
  regression tests follow the new API (`uom_id`, `partner_id`).

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.

19.0.1.0.0
----------

- The vendor field on the replenishment wizard was absorbed by Odoo standard
  (`purchase_stock`, `stock.replenish.mixin`). The Deltatech override was
  removed: keeping it would have rendered the field twice in the wizard form.
- The module is kept installable, without content, so that databases upgraded
  from 18.0 do not lose the module entry.
