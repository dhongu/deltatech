This module works automatically, with no configuration needed.

- Open **Purchase > Orders** (or the RFQ list): a new **Delivery Status** badge
  column is shown, next to the order state, with two possible values:
  - **In Progress** — the order has at least one incoming shipment that is not
    yet done or cancelled.
  - **Done** — all related receipts are done or cancelled (or the order is
    confirmed and has no receipts at all, e.g. a services-only order).
- The same badge is also shown on the Purchase Order form, next to **Source
  Document**.
- Use the new **Done** / **In progress** filters in the Purchase Orders search
  view to quickly find orders by delivery status.
