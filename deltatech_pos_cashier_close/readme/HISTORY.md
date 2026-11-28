## 20.0.1.0.1 (2026-11-28)

- Migrated to Odoo 20.0: *Close Register* goes to the pos_hr *Cashier* role through
  `PosAccessRightPlugin.canCloseSession`; *Restrictive* and *Supervised* never get it.

## 19.0.1.0.1 (2026-11-28)

- Romanian translation.
- Description: Cash In/Out is not among the manager rights in Odoo 19 (it follows the Odoo
  user of the register), so it is no longer listed there.
- Consultant sheet (RO), usage with screenshots and demo GIF for the Apps Store.

## 19.0.1.0.0 (2026-10-23)

- First version: *Cashiers Close the Register* option, per register, that gives *Close
  Register* to the employees with basic rights without the other manager rights.
