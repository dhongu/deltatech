## 18.0.1.0.9

- Fix `default_code` uniqueness check: only active products conflict with each
  other. The check now forces `active_test=True` in its lookup, so an ambient
  `active_test=False` context (e.g. during a marketplace/Shopify import) no
  longer makes an archived product collide with a newly created active one.
  Uniqueness stays over `(default_code, active, company_id)`, matching
  `show_not_unique`.

## 18.0.1.0.8

- Batch-safe uniqueness constraint (single indexed query) and index on
  `default_code`.

## 18.0.1.0.7

- Correct internal-code uniqueness for shared products (NULL company).
