Modulul nu adaugă interfață proprie: el doar pune câmpurile la dispoziție.

**Ca să scrii în ele** (driver de casă de marcat), moștenește mixinul pe modelul tău:

```python
class MyModel(models.Model):
    _name = "my.model"
    _inherit = ["my.model", "deltatech.ecr.fiscal.mixin"]
```

**Ca să le citești**, e destul să declari `deltatech_ecr_fiscal` în `depends` — nu ai
nevoie de modulele de casă de marcat.
