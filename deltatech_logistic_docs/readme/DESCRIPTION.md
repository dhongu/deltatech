Shipping documents such as CMRs, certificates of origin or signed delivery notes are
often attached to a different record than the one the user has open: the CMR on the
delivery, the certificate on the purchase order, the vendor's PDF on the bill. This
module shows, from any document in the flow, the files attached to the related
documents as well.

**Documents smart button**: a **Documents** button is added to the form of the sales
order, the purchase order, the transfer and the invoice or bill. It shows the number of
attachments found along the flow and opens them in a kanban, list or form view.

**Attachments collected along the flow**:

- *Sales order*: its own attachments, those of its transfers and those of its invoices.
- *Purchase order*: its own attachments, those of its receipts and those of its bills.
- *Transfer*: its own attachments, those of the related sales or purchase order and
  those of the order's invoices or bills.
- *Invoice or bill*: its own attachments and those of the sales and purchase orders
  linked to its lines, together with their transfers. For other journal entries only
  the entry's own attachments are counted.

**New files on the right document**: an attachment created from the view opened by
the button is linked by default to the document the button was clicked on.

**Download button**: the attachment kanban card gets a **Download** button. Files with
the `.zplpdf` extension are downloaded as raw data, for label printers.

The module adds no menu and needs no configuration.
