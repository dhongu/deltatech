Features:
 - an invoice can be created from one or more pickings
 - an invoice can be created from a batch
 - only the products in the picking(s) with their respective done quantities will be added to the invoice
 - only pickings that come from a sale order (delivery or returns) can be invoiced
 - a picking must be in "done" state to be invoiced
 - a "to invoice" field is added to pickings, for filtering purposes. When a sale picking is created, the field is set to True. When an invoice is created, the field is set to False. When an invoice is cancelled or deleted, it's set to True
 - a field with link to the invoice is added to pickings. The field is computed to point to the invoice generated from the picking
 - **Modifications to product lines in invoices created from pickings are restricted.**
