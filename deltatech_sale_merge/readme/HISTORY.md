## 20.0.1.0.0 (2026-11-21)

- Migration to Odoo 20.0: access rights in `ir.access`.
- Fix: a salesman without invoicing rights can merge quotations again; the started-payment check
  reads `transaction_ids` (invoicing users only) with system rights (dhongu/deltatech#4297).

## 19.0.1.0.0

- Add: wizard *Merge orders* on the quotations list, with target (oldest, selected or new), add up or keep lines, optional section per quotation, and links *Merged Into* / *Merged From* on the cancelled quotations.
- Add: consultant sheet with screenshots, English usage guide with screenshots and demo GIF.
