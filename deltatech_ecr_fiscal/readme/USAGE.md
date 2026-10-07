The module adds no screens of its own: it only provides the fields.

**To write them** (a cash register driver), inherit the mixin on your model:

```python
class MyModel(models.Model):
    _name = "my.model"
    _inherit = ["my.model", "deltatech.ecr.fiscal.mixin"]
```

**To read them**, declaring `deltatech_ecr_fiscal` in `depends` is enough; the cash register
modules are not needed.
