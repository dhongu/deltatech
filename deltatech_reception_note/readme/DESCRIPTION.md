Receives goods from a vendor on reception notes that draw on the open quantities of several purchase
orders at once, instead of validating the receipt of each order separately. Useful when one delivery
covers several orders, or one order arrives in several deliveries.

**Purchase order types.** Every purchase order gets a *Type*:

- *Normal*: the standard order;
- *RFQ Only*: a request that keeps the quantities still expected from the vendor; it cannot be
  confirmed and has a *Set as sent* button;
- *Reception Note*: the delivery actually received, with the vendor's *Delivery Note No*.

**Create reception note.** On a *Normal* purchase order, *Actions > Create reception note* moves its
open quantities to a new *RFQ Only* order in the *RFQ Sent* state: same vendor, company, currency,
fiscal position, payment terms, prices and taxes, and the quantity not received yet on each line. The
receipts of the source order that are *Ready* are cancelled, so the goods are received only through
reception notes.

**Reception note.** A purchase order of type *Reception Note* holds the products and quantities
delivered. When it is confirmed, its quantities are taken from the sent *RFQ Only* orders of the same
vendor and company, oldest first, in the unit of measure of the product, and the receipt is created by
the standard confirmation. An *RFQ Only* order that is fully consumed is marked as empty.

**Ignore quantities.** If a product or a quantity is not found on a sent *RFQ Only* order, the
confirmation stops with a message. Tick *Ignore quantities* on the reception note to confirm it anyway;
the forced quantities are listed in the chatter.

**Menus and filters.** *Purchase > Reception notes* has three entries:

- *Prepare reception note*: the reception notes not confirmed or invoiced yet;
- *To arrive*: incoming transfers in the *Ready* state;
- *To invoice*: incoming transfers in the *Done* state.

The purchase lists show the *Type* and *Date sent* as optional columns, and the search has the *Not
empty* and *Empty* filters for *RFQ Only* orders.

## Limitations

- The module adds no printed document of its own: a reception note is printed with the standard
  purchase order reports.
- *To invoice* lists every done incoming transfer, whether it was invoiced or not.
