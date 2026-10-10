## 20.0.0.0.2 (2026-10-10)

- Fix SALECUR-001: when the invoice date or currency changes, the sale line price is first
  converted from the sale line unit of measure into the invoice line unit of measure, then
  into the invoice currency (e.g. 10 per Unit becomes 120 per Dozen, not 10 per Dozen).

## 19.0.0.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
