Technical base module, shared by the tools that import vendor invoices in UBL XML format.
It has no menu, view or setting of its own and changes nothing in the standard flows.

It provides an abstract model with:

- **UBL reading**: document header (number, dates, currency, order reference, totals,
  supplier VAT and name; a credit note is recognized by its document type or type code 381)
  and invoice lines (`InvoiceLine`: supplier code, barcode, name, quantity, unit, price,
  discount from `AllowanceCharge`, VAT rate and category).
- **Vendor lookup** by VAT number (a Romanian CUI with or without the `RO` prefix) or by name.
- **Product matching** by barcode, supplier code, internal reference, supplier product name
  or product name, reporting how each product was found.
- **Unit conversion** from UBL unit codes (C62, KGM, LTR, ...) to Odoo units.
- **Vendor price update** in the vendor pricelist and **product creation** from an invoice line.
- **Duplicate bill lookup** and the reading of the VAT rate declared on each line.

Used by *Purchase UBL Import* (`deltatech_purchase_ubl`) and *Vendor Bill UBL Review*
(`deltatech_vendor_bill_ubl_review`).
