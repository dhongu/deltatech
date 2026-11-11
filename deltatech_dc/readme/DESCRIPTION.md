Customers often ask suppliers for a declaration that delivered goods meet their technical standards. This module stores each product's quality references and prints a numbered Declaration of Conformity for lots, invoices and deliveries.

- **Quality references**: A *Quality Control* tab on the product holds *Standard of Company*, *Data Sheet*, *Technical Specification* and *Standards*, printed when filled in.
- **Declaration records**: A *Declaration of Conformity* list (Sales product catalog menu) shows *Number*, *Date of Declaration*, *Product* and *Lot*. Printing numbers them from the `DC/` sequence; by hand, you type the number.
- **Print and create**: The print action on a lot, a posted invoice or a delivery creates the missing declarations and prints them: one per lot, or per product and date without a lot. Services are skipped.
- **Production date**: The lot's *Production Date* dates its declaration (today when empty) and prints as the quality plan date for lots with an expiration date.
- **Second delivery form**: *Declaration of Conformity 2* on a delivery prints one declaration for all its lines, with product, quantity, lot, use date and storage conditions, and creates no records.

The module depends on Sales, Manufacturing, `product_expiry` and `stock_account`. Internal users can edit declarations of their companies. The wording is fixed in the templates; the second form reads a partner *NRC* field that this module does not add.
