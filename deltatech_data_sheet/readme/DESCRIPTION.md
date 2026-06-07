Attach product documentation — technical data sheets and safety data sheets — directly to product records in Odoo, making the PDFs accessible from the product form for sales and logistics teams.

**Key features:**

- Adds a **Data Sheet** group on the product form (after the Description group) with two PDF attachment fields.
- **Data Sheet Attachment** — links a public PDF attachment (e.g. technical specifications, product catalogue page).
- **Safety Data Sheet** — links a public PDF attachment for MSDS / SDS compliance documents.
- Both fields accept only public PDF attachments (`application/pdf`, `public = True`), ensuring the documents can be shared safely with customers and portals.
- Fields are stored on `product.template` and are therefore shared across all product variants.
