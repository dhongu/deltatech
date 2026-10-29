## 19.0.1.0.1 (2026-10-29)

- Development status set to **Production/Stable**.

## 19.0.1.0.0 (2026-10-29)

- First version. New `attribute_role` selection on `product.attribute` (empty, extended
  by other modules with `selection_add`), unique per role, shown in the attribute form
  and list.
- Lookups `product.attribute._get_attribute_by_role(role)` and
  `product.product._get_attribute_value_by_role(role)`.
