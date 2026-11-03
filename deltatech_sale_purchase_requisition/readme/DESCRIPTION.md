Starts requests for quotation to vendors straight from a sales quotation, so the buyer can price the
products before the quotation goes to the customer, and keeps the RFQs linked to the quotation.

**Create RFQ.** A *Create RFQ* button in the header of a quotation (states *Quotation* and *Quotation
Sent*) opens a new purchase order form, not saved yet, prefilled with:

- the quotation lines that can be purchased (*Purchase* ticked on the product) and have a quantity
  above zero, with their description, unit of measure and quantity;
- the quotation number as *Source* and the quotation company.

Sections and notes are skipped. The buyer picks the vendor, checks the prices and saves the RFQ. The
button can be used again for other vendors, so the same quotation can be priced by several vendors.

**Linked RFQs.** Every RFQ started this way keeps the quotation it came from. An *RFQs* smart button on
the quotation shows how many there are and opens them, or opens the RFQ directly when there is only
one.

**Access.** The button is shown to users with purchase rights (*Purchase*: *User* or *Administrator*).

No purchase agreement is created and the *Purchase Agreements* module is not needed.
