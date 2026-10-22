## 19.0.1.2.9 (2026-10-22)

- Listed on Odoo Apps as *Purchase Order Phases* (was *Purchase Order Stage*). The technical name `deltatech_purchase_phase` does not change.

## 19.0.1.2.8 (2026-10-17)

- A missing phase (for example after deleting the RFQ phase) is now created automatically also for users who are not purchase managers, instead of blocking the RFQ sending, the confirmation or the receipt update with an access error.
- New default phase "Refused", used when the delivery status of a receipt becomes refused.

## 19.0.1.2.7 (2026-09-29)

- Own module icon, instead of the generic gears it had.
