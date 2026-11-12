## 20.0.1.0.0 (2026-11-12)

- Port to 20.0: no `base_vat` (merged into `base`), the company is recognised by its VAT
  number (`is_company` is computed), the mandatory registered office fields come from
  `res.partner`, the city is typed as text also when the country enforces a choice from
  the city list.
- Fix: a company already recorded with the CUI typed is shown, selected, among the billing
  addresses of the checkout page; before, no billing address was selected and the order
  could not be confirmed.

## 19.0.1.0.0 (2026-11-12)

- First version: checkout address in the Romanian order (last name and first name, country,
  county, city, street, email, phone) and an optional *Billing details* section that invoices
  the order to a company: created from the name and the CUI typed, or the company already
  recorded with that CUI, without attaching the customer to it.
