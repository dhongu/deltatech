## 19.0.0.0.2 (2026-08-21)

- Add: `website.show_line_subtotals_tax_selection` ("Display Product Prices") is a computed+stored field with no Romanian override, so `website_sale` resets it to `tax_excluded` on every recompute of `company_id.account_fiscal_country_id` - triggered, for example, by any write on the company's own partner address (e.g. a nightly ANAF partner sync). The new `Website._compute_show_line_subtotals_tax_selection` override preserves the previously saved value instead of letting it reset silently, without forcing either option.

## 19.0.0.0.1 (2026-08-13)

- Fix: `_validate_address_values` still required `is_main_address`, a parameter Odoo 19 no longer passes - the 19.0 migration kept the 18.0 signature. Any address submitted from the website raised a `TypeError` (500) as soon as this module was installed. The parameter is dropped; anything else the caller adds still travels through `**_kwargs`.
