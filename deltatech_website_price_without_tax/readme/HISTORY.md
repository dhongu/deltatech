# History

## 19.0.1.0.4 (2026-09-26)

- Fix: upgrade from 18.0 failed with "Element `<xpath expr="//div[@itemprop='offers']">`
  cannot be located in parent view". The generic view kept its 18.0 arch in the
  database and had a website-specific (COW) copy. On update, the COW copy is written
  first and its validation combines the still-old generic view against the 19.0
  `website_sale.product_price`. A pre-migration script now deactivates the old generic
  view and an end-migration script reactivates it once the new arch is loaded. The
  website-specific copies are left untouched, so the option stays enabled or disabled
  per website as the customer set it in the website editor.
