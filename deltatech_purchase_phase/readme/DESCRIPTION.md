Overview

This module adds a lightweight phase/stage tracking on purchase orders. It introduces
configurable phases and keeps the current phase on each `purchase.order`, with optional
automatic transitions aligned with Odoo’s document `state`.

Key features

- Phase on Purchase Orders
  - New field `phase_id` on `purchase.order` (tracked in the chatter) to indicate the
    current phase of the document.

- Automatic phase changes
  - When the RFQ is sent (`state = sent`), the phase is set to the phase with code `rfq`.
  - When the PO is confirmed (`state = purchase`), the phase is set to the phase with
    code `purchase_confirm`.
  - If a referenced phase code does not exist, it will be created on the fly with the
    same code and name.

- Manual control and auditing
  - Users can manually change the phase on the Purchase Order form.
  - Changes to `phase_id` are tracked for auditability.

Configuration

1) Go to: Purchase → Configuration → Purchase Order Phases
2) Create or adjust the phases you need:
   - Code: unique technical key (e.g., `draft`, `rfq`, `purchase_confirm`, `done`).
   - Name: human-readable label shown to users.

Usage

- Open any Purchase Order and set the Phase. The field is tracked in the chatter.
- On sending an RFQ or confirming the order, the phase may update automatically as
  described above. You can still override it manually afterwards.
- For data loads or special flows where you want to skip auto-updates, pass context
  `{"skip_phase_update": True}` to writes on `purchase.order`.

Technical notes

- Models/fields
  - `purchase.order`:
    - `phase_id = fields.Many2one("purchase.order.phase", tracking=True, copy=False)`
  - Helper API: `set_phase(code)` sets/creates the phase by its `code` and writes it
    on the current order(s).

- Behavior hooks
  - `write()` override updates the phase when `state` transitions to `sent` or `purchase`.
  - Context key `skip_phase_update` prevents automatic changes during programmatic writes.

Dependencies and compatibility

- Depends on `purchase_stock`
- Designed to be non-invasive: it does not alter the standard state machine of Purchase
  Orders; it only adds complementary phase tracking.

Limitations and extensions

- Out of the box, automatic transitions are defined for `rfq` and `purchase_confirm`.
  You can extend this behavior via studio, server actions, or small Python overrides to
  cover additional states (e.g., `done`, `cancel`).

