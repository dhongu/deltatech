Modulul nu adaugă ecrane proprii: doar pune câmpurile la dispoziție.

**Ca să scrieți în ele** (un driver de casă de marcat), moșteniți mixinul pe modelul dumneavoastră:

```python
class MyModel(models.Model):
    _name = "my.model"
    _inherit = ["my.model", "deltatech.ecr.fiscal.mixin"]
```

**Ca să le citiți**, e suficient să declarați `deltatech_ecr_fiscal` în `depends`; modulele de casă
de marcat nu sunt necesare.
