In Odoo 19, the "Create Bill" button on the purchase order form was replaced by an
"Upload Bill" widget that requires selecting a file before a bill can be created.

This module restores the classic one-click "Create Bill" button next to the upload
widget, so purchase orders can still be invoiced directly, without attaching a file,
exactly as in Odoo 18.

Odoo 19 also dropped the automatic copy of the purchase order's "Vendor Reference"
into the vendor bill's "Reference" and "Payment Reference" fields when a bill is
created from a purchase order. This module restores that copy as well, matching the
Odoo 18 behavior.

The same applies to the purchase order list: in Odoo 19 the "Create Bills" header
button was kept only on the "Purchase Orders" list, while the Requests for Quotation
list (the default dashboard list) lost it. This module restores it there as well, so
several purchase orders can be selected and billed in one go — including returns,
which Odoo converts automatically into a vendor credit note when the total is negative.
