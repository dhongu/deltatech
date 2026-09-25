## 19.0.0.0.5 (2026-09-25)

- Security: `_validate_address_values` no longer runs the duplicate check
  (VAT, email, phone) for the public user. An anonymous visitor could submit
  `/shop/address/submit` with any email or phone and learn from the "An other
  partner already exists with the same ..." error whether it belonged to an
  existing customer. It also blocked existing customers from checking out as
  guests. Logged-in users keep the duplicate check; the VAT format and ANAF
  validation are unchanged for everyone.

## 19.0.0.0.4 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.

## 19.0.0.0.3 (2026-09-23)

- Overrides that call `super()` without returning its result now pass it on
  (pylint-odoo `missing-return`). The parent methods return `None` today, so the
  behavior is unchanged.

## 19.0.0.0.2 (2026-08-21)

- Add: `website.show_line_subtotals_tax_selection` ("Display Product Prices") is a computed+stored field with no Romanian override, so `website_sale` resets it to `tax_excluded` on every recompute of `company_id.account_fiscal_country_id` - triggered, for example, by any write on the company's own partner address (e.g. a nightly ANAF partner sync). The new `Website._compute_show_line_subtotals_tax_selection` override preserves the previously saved value instead of letting it reset silently, without forcing either option.

## 19.0.0.0.1 (2026-08-13)

- Fix: `_validate_address_values` still required `is_main_address`, a parameter Odoo 19 no longer passes - the 19.0 migration kept the 18.0 signature. Any address submitted from the website raised a `TypeError` (500) as soon as this module was installed. The parameter is dropped; anything else the caller adds still travels through `**_kwargs`.
