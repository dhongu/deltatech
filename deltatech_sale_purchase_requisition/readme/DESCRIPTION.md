This module adds a button on the Sales Quotation to create Purchase RFQ(s)
from the quotation lines and links those RFQs back to the quote.

Key points:
- Works with alternative purchase orders (no Purchase Requisition used).
- Opens the Purchase Order form in create mode, prefilled with eligible
  products from the quotation (no automatic creation).
- The buyer selects the vendor and saves the RFQ (draft PO).
- A smart button on the quotation shows and opens the linked RFQs.

Eligibility rules for lines:
- Product must be purchasable (`purchase_ok = True`).
- Quantity must be strictly greater than 0.
- Section/note/display lines are ignored.

User interface:
- Header button on Sales Quotation: "Create Purchase Order(s)".
- Smart button: "Purchase Orders" with the count of linked RFQs.

This keeps the flow simple and aligned with the standard alternative
purchasing approach in Odoo, without introducing purchase agreements.
