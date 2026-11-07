The module adds no screens of its own: it only provides the fields. They are shown on the invoice
form by the module that prints the receipt from the invoice (`deltatech_sale_store`). On the POS order
`deltatech_pos` fills them in without showing them; use **Actions → Export** to read them.

**Simulated receipt** (`fiscal_simulated`) is meant to be ticked by the cash register driver when the
receipt was printed on a simulated register: the emulator in Odoo, or Terrabit Connect in simulation mode (the
station shows a **Simulation** ribbon, see `deltatech_tc`). Such a receipt is not a fiscal document,
even when its BF, NR and Z numbers are filled in. In this version the field is only provided: the
drivers do not set it yet and the compliance modules do not read it yet.

**To write them** (a cash register driver), inherit the mixin on your model:

```python
class MyModel(models.Model):
    _name = "my.model"
    _inherit = ["my.model", "deltatech.ecr.fiscal.mixin"]
```

**To read them**, declaring `deltatech_ecr_fiscal` in `depends` is enough; the cash register
modules are not needed.
