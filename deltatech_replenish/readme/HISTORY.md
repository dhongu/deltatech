19.0.1.0.0
----------

- The vendor field on the replenishment wizard was absorbed by Odoo standard
  (`purchase_stock`, `stock.replenish.mixin`). The Deltatech override was
  removed: keeping it would have rendered the field twice in the wizard form.
- The module is kept installable, without content, so that databases upgraded
  from 18.0 do not lose the module entry.
