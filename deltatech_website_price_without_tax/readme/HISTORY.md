# 19.0.1.0.6

- Fix: the "Price without tax" shown on the product page was wrong when the website
  display mode and the tax "included in price" setting differed. With prices displayed
  tax included and a tax excluded from price, the gross price was shown as net (121
  instead of 100); with prices displayed tax excluded and a tax included in price, the
  net price was reduced again (82.64 instead of 100). The net price now follows the
  website display mode: it is taken as is when prices are shown tax excluded, and the
  taxes are removed from the displayed gross price otherwise.

# 19.0.1.0.5

- Own module icon, instead of the generic gears it had.

# History

## 20.0.1.0.7 (2026-10-22)

- Listed on Odoo Apps as *Price Without Tax on Website* (was *eCommerce Product Price Without Tax*). The technical name `deltatech_website_price_without_tax` does not change.

## 19.0.1.0.4 (2026-09-26)

- Fix: upgrade from 18.0 failed with "Element `<xpath expr="//div[@itemprop='offers']">`
  cannot be located in parent view". The generic view kept its 18.0 arch in the
  database and had a website-specific (COW) copy. On update, the COW copy is written
  first and its validation combines the still-old generic view against the 19.0
  `website_sale.product_price`. A pre-migration script now deactivates the old generic
  view and an end-migration script reactivates it once the new arch is loaded. The
  website-specific copies are left untouched, so the option stays enabled or disabled
  per website as the customer set it in the website editor.
