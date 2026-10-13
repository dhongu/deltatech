## 19.0.1.0.4 (2026-10-02)

- Fix the "Is ready" filter on sale orders: it returned exactly the orders that are not ready (the ORM sends the `in` operator, the search method only handled `=`). `=`, `!=`, `in` and `not in` are now handled; the tests check the result.

## 19.0.1.0.3 (2026-09-29)

- Own module icon, instead of the generic gears it had.
