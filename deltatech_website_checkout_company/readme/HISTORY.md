## 20.0.1.0.0 (2026-11-12)

- Port to 20.0: no `base_vat` (merged into `base`), the company is recognised by its VAT
  number (`is_company` is computed), the mandatory registered office fields come from
  `res.partner`, the city is typed as text also when the country enforces a choice from
  the city list.
- Company billing only for deliveries in Romania; consultant sheet (from 19.0).
- For a CUI already recorded, the company itself or an invoice address under it with the
  same name and registered office is reused instead of adding a duplicate (from 19.0).
- The county of the registered office is accepted only from Romania.
- Consultant sheet and usage describe the reuse of the invoice address.

## 19.0.1.0.0 (2026-11-12)

- First version: checkout address in the Romanian order (last name and first name, country,
  county, city, street, email, phone) and an optional *Billing details* section that invoices
  the order to a company: created from the name, the CUI and the registered office typed, or,
  for a CUI already recorded, a new invoice address under that company with the typed data,
  without attaching the customer to it and without showing the recorded company data.
