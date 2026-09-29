## 19.0.1.1.0 (2026-09-29)

- The cards share the whole width of the page, with no empty space at the end of the row.
- Large numbers fit on a card: from 100,000 on, amounts and counts are shown in thousands or
  millions (1.9M lei, 123.5k), with Odoo's own compact format; `formatKpiAmount` and
  `formatKpiCount` do it for the modules that build the cards, and a card's `title` (its
  tooltip) can carry the exact value.

## 19.0.1.0.0 (2026-09-28)

- First release: the KPI cards and their search filter binding, taken out of
  `deltatech_delivery_dashboard` so that other dashboards share the same look and behaviour.
