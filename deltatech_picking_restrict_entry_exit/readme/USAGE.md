This module enforces, for Receipts and Deliveries (not for returns or backorders),
that every move line is backed by a sale/purchase order and stays within the ordered
quantity:

- **On Validate**: a delivery (outgoing) move must be linked to a sale order line,
  and a receipt (incoming) move must be linked to a purchase order line, otherwise
  validation is blocked with an error naming the product. The done quantity of any
  line also cannot exceed the quantity ordered. Internal transfers are only checked
  when source and destination are in *different* warehouses; moves within the same
  warehouse are exempt.
- **On Save**: the same quantity-vs-demand check runs when you edit the operations
  lines directly on the transfer, before validation. In addition, manually adding a
  brand-new line to an incoming/outgoing transfer is blocked unless the current user
  belongs to the **Picking create permission** group.
- The **Picking create permission** group (Settings > Users & Companies > Groups,
  hidden category) is assigned by default only to the Administrator/OdooBot users
  when the module is installed. To let other users bypass these restrictions, add
  them to this group from the Groups list (it doesn't show on the normal Users
  form, since its category is hidden).
