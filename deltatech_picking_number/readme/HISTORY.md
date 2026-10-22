## 19.0.1.0.1 (2026-10-22)

- Listed on Odoo Apps as *Transfer Numbering on Demand* (was *Picking Number*). The technical name `deltatech_picking_number` does not change.

## 19.0.1.0.0 (2026-10-17)

- Migration to 19.0.
- "Allocate number" works on a set of transfers: each transfer without a request number gets its own number from the operation type's request sequence (on 18.0 the action assumed a single transfer).
- The "document has been numbered" error uses `self.env._` (the translation is unchanged).
