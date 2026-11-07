The module adds no screens of its own: it only provides the fields. They are shown on the invoice
form by the module that prints the receipt from the invoice (`deltatech_sale_store`). On the POS order
`deltatech_pos` fills them in without showing them; use **Actions → Export** to read them.

**Simulated receipt** (`fiscal_simulated`) is ticked by the cash register driver when the
receipt was printed on a simulated register: the emulator in Odoo, or Terrabit Connect in simulation mode (the
station shows a **Simulation** ribbon, see `deltatech_tc`). Such a receipt is not a fiscal document,
even when its BF, NR and Z numbers are filled in. The POS (`deltatech_pos`) and the store print action
(`deltatech_sale_store`) set it; `l10n_ro_pos_fiscal_compliance_ecr` keeps such receipts out of the Z
report and of the AMEF journal.

**To write them** (a cash register driver), inherit the mixin on your model:

```python
class MyModel(models.Model):
    _name = "my.model"
    _inherit = ["my.model", "deltatech.ecr.fiscal.mixin"]
```

**To read them**, declaring `deltatech_ecr_fiscal` in `depends` is enough; the cash register
modules are not needed.
