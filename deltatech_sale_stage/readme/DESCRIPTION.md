This module helps your sales team stay on top of every order by introducing a **customizable phase system** for sale orders.

Instead of relying only on Odoo's standard statuses (Draft, Confirmed, Done), your team can define their own internal phases — such as *Confirmed*, *Prepared*, *Shipped*, *Delivered* — and track exactly where each order stands in your fulfillment process.

### Key Business Benefits

- **Full visibility for back-office teams**: Each sale order displays its current phase as a colored badge, making it easy to spot orders that need attention at a glance.

- **Flexible phase configuration**: Define as many phases as your business needs. Assign each phase a name, a color, and a sequence. Phases are managed from Sales → Configuration → Sale Order Phases.

- **Automatic phase progression**: Phases advance automatically as the order moves through the standard Odoo workflow:
  - When a quotation is sent to the customer → order moves to the *Sent* phase
  - When an order is confirmed → order moves to the *Confirmed* phase
  - When an order is invoiced → order moves to the *Invoiced* phase
  - When an order is cancelled → order moves to the *Cancelled* phase

- **Delivery-driven phase updates**: When a shipment is validated or its delivery status changes (e.g., picked up by courier, delivered to customer, refused), the linked sale order phase is updated automatically — no manual intervention needed.

- **Trigger automated actions**: Each phase can have an optional server action attached. When an order enters that phase, the action runs automatically — useful for sending notifications, updating records, or triggering integrations.

- **Enforce order workflow**: If a phase marked as *Confirmed* is manually set on a draft order, the order is automatically confirmed. If a phase marked as *Cancelled* is set, the order is cancelled — keeping your data consistent.

- **Search and group by phase**: Filter and group sale orders by phase directly from the list view, making it easy to manage workload and prioritize tasks.

### How It Works with Deliveries

Each warehouse operation type (e.g., delivery orders) can have a default phase assigned. When a delivery of that type is validated, the linked sale order automatically advances to that phase. Additionally, real-time courier status updates (via `deltatech_delivery_status`) trigger further phase changes:

- Parcel picked up / in transit → *Shipped*
- AWB generated → *Pre-advice*
- Delivered to customer → *Delivered*
- Refused by customer → *Refused*
