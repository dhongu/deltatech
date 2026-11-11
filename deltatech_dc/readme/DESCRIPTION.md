Customers often ask for a declaration that delivered goods meet their technical standards. This module stores each product's quality references and prints a numbered Declaration of Conformity for lots, invoices and deliveries.

- **Quality references**: A *Quality Control* tab on the product holds *Standard of Company*, *Data Sheet*, *Technical Specification* and *Standards*, printed when filled in.
- **Declaration records**: A *Declaration of Conformity* list (Sales product catalog menu) shows *Number*, *Date of Declaration*, *Product* and *Lot*. Printing numbers them from the `DC/` sequence.
- **Print and create**: Printing from a lot, a posted invoice or a delivery creates the missing declarations, one per lot or per product and date without a lot. Services on invoices are skipped.
- **Production date**: The lot's *Production Date* dates its declaration and, for lots with an expiration date, prints as the quality plan date. Lot and invoice prints need it; delivery prints use today when it is empty.
- **Second delivery form**: *Declaration of Conformity 2* on a delivery prints one declaration for all its lines, with product, quantity, lot, use date and storage conditions, and creates no records.

The module depends on Sales, Manufacturing and `product_expiry`. Internal users can edit declarations of their companies. Both printed forms use fixed wording and read a partner `nrc` field that this module does not add.
