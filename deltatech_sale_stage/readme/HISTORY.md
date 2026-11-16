## 19.0.1.2.10 (2026-11-13)

- Fix: posting an invoice linked to a sale order no longer raises `AccessError` on `sale.order.phase` for users without sales rights (e.g. accountants); only reading the phases and writing `phase_id` use elevated rights; the phase server action, confirmation and cancellation still run with the current user's rights.

## 19.0.1.2.9 (2026-10-22)

- Listed on Odoo Apps as *Sale Order Phases* (was *Sale Order Stage*). The technical name `deltatech_sale_stage` does not change.

## 19.0.1.2.8 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.1.2.7 (2026-09-29)

- Own module icon, instead of the generic gears it had.
