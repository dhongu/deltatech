This module extends the functionality of the delivery system in Odoo to provide enhanced tracking and status management for shipments.

Delivery status tracking

- Every stock picking gets a **Delivery Status** field (`delivery_state`) that follows the shipment through Draft, Ready in warehouse, Pre advice, In Transit, In Carrier Warehouse, In delivery and Delivered. It is visible on the picking form and list, and can be used to group/filter pickings (**Filters > Delivery Status**).
- Pickings also show an **Availability** badge (Available / Partially available / Unavailable) with matching filters in the picking search view.

Postponing deliveries

- On a picking, the **Postponed** checkbox manually blocks the delivery; a "Postponed" ribbon appears on the picking form when active.
- On a payment provider (**Accounting/Sales > Configuration > Payment Providers**), enable **Postponed Delivery** so that any order paid through it is automatically blocked until the payment is confirmed; the block is released automatically once payment is received.
- On a Sales Team (**Sales > Configuration > Sales Teams**), enable the wire-transfer postponement option so orders paid by wire transfer from that team are postponed until the transfer is confirmed.
- Operation type settings (**Inventory > Configuration > Operations Types**) also expose a **Postponed** flag.
