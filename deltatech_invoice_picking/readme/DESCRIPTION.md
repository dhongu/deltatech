- Features:

  - an invoice can be created from one or more pickings
  - an invoice can be created from a batch
  - only the products in the picking(s) with their respective done quantities will be added to the invoice
  - only pickings that come from a sale order or purchase orders can be invoiced
  - a picking must be in "done" state to be invoiced
  - a "to invoice" field is added to pickings, for filtering purposes. When a picking that comes from a sale or purchase
    order is validated, the field is set to True. When an invoice is created, it is set to False. When the invoice is
    cancelled or deleted, it is set back to True and the link to the invoice is cleared
  - a field with link to the invoice is added to pickings. The field is computed to point to the invoice generated from
    the picking
  - **on an invoice created from pickings, the quantity or product of storable product lines cannot be changed and
    those lines cannot be deleted, so the invoice stays aligned with the delivered quantities**
