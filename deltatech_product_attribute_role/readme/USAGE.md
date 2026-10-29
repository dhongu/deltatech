In a module that needs a role, extend the selection and look the attribute up by role:

``` python
class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    attribute_role = fields.Selection(
        selection_add=[("variety", "Variety")],
        ondelete={"variety": "set null"},
    )
```

- `product.attribute._get_attribute_by_role("variety")` returns the attribute holding
  the role;
- `product.product._get_attribute_value_by_role("variety")` returns the variant's value
  for it;
- in domains, filter on `attribute_id.attribute_role`, e.g.
  `[('attribute_id.attribute_role', '=', 'variety')]` on `product.attribute.value`.

Users then pick the attribute's role in the attribute form, once per database.
