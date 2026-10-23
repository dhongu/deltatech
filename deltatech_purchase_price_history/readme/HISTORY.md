## 19.0.1.0.1 (2026-10-23)

- New module icon and main image for the Odoo Apps Store (banner).

## 19.0.1.0.0 (2026-10-17)

- Migration to 19.0.
- The raw query that fills the minimum, maximum and average purchase prices
  is built with `SQL()`, and the cached values of the product templates are
  invalidated after the update, so the form shows the new prices right away.
- The test now checks the computed prices (10, 20 and 15 for two vendor bills
  of 10 and 20).
