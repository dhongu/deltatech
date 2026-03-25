Features:

- Adds a configurable **phase system** for sale orders, allowing back-office teams to track the internal progress of each order through custom-defined stages.

- Introduces the `sale.order.phase` model with the following configurable attributes per phase:
  - **Name** and **sequence** (ordering of phases)
  - **Color** (displayed as a colored badge in list and form views via the `many2one_badge` widget)
  - **Code** (used for programmatic phase lookup)
  - **Boolean flags**: `confirmed`, `send_email`, `pre_advice`, `shipped`, `delivered`, `refused`, `invoiced`, `paid`, `canceled` — each flag marks the semantic meaning of the phase
  - **Server Action** (`action_id`): an optional `ir.actions.server` that is automatically executed when the order enters this phase

- Adds a `phase_id` (Many2one) field on `sale.order`, displayed as a colored badge using the `deltatech_widget_many2one_badge` widget. The phase is tracked in the chatter.

- Automatic phase transitions are triggered by standard sale order workflow events:
  - **Quotation sent** → phase flagged as `send_email`
  - **Order confirmed** → phase flagged as `confirmed`
  - **Order cancelled** → phase flagged as `canceled`
  - **Order invoiced** → phase flagged as `invoiced`

- The `set_phase(phase_step)` method provides a flexible API for setting the phase:
  - Accepts either a **boolean flag name** (e.g., `"confirmed"`, `"shipped"`) or a **phase code** (e.g., `"pre_advice"`)
  - Respects the **sequence order**: a phase is only applied if its sequence is higher than the current phase (unless `ignore_sequence=True` is passed)
  - If the order has a completed payment transaction, it prefers a phase marked as `paid`

- Integration with **stock pickings** (`stock.picking`):
  - Each operation type (`stock.picking.type`) can have a default `phase_id` assigned; when a picking of that type is validated (`_action_done`), the linked sale order is automatically moved to that phase.
  - Phase transitions are also triggered by changes to the `delivery_state` field (provided by `deltatech_delivery_status`):
    - `in_transit`, `in_warehouse`, `in_delivery` → phase flagged as `shipped` (sequence ignored)
    - `delivered` → phase flagged as `delivered`
    - `pre_advice` → phase flagged as `pre_advice`
    - `refused` → phase flagged as `refused` (sequence ignored)

- When a phase is set manually or automatically, the associated **server action** is executed automatically (with error logging on failure).

- Bidirectional workflow enforcement via `write`:
  - If a phase marked as `confirmed` is set on a draft order, the order is automatically confirmed.
  - If a phase marked as `canceled` is set on a non-cancelled order, the order is automatically cancelled.

- Adds a **configuration menu** under Sales → Configuration → Sale Order Phase for managing phases.

- Extends **list views** (orders and quotations) and the **form view** of `sale.order` to display the current phase as a colored badge.

- Adds a **search filter** and **group-by option** by phase in the sale order search view.

- Depends on: `sale_stock`, `deltatech_delivery_status`, `deltatech_widget_many2one_badge`.
