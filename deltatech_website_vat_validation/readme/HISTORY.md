## 19.0.0.1.0 (2026-10-11)

- The ANAF data no longer overwrites what the customer typed: the street, city, zip and county
  from ANAF fill only the empty fields. The partner name stays the legal name of the company from
  ANAF, the name the invoice (e-Factura) is issued to; with `l10n_ro_website_anaf_prefill` the
  customer sees it before submitting.
- A struck-off company (registration state "RADIERE" at ANAF) is refused: it no longer exists and
  cannot be the buyer.
- A fiscally inactive company can order; the cart gets an internal note for the salesperson
  (VAT code cancelled: invoice with VAT, without reverse charge, check the collection).

## 19.0.0.0.9 (2026-10-11)

- Duplicate check of a logged-in customer, clearer and fairer:
  - a tax code (VAT) already used by another customer now says what to do: ask a colleague who
    has access, or send an access request from the /b2b page (with `deltatech_b2b_portal`), or
    contact us. Before: "An other partner already exists with the same ...";
  - an e-mail address of another account asks to log in with that account or use another address;
  - the tax code is compared without its country prefix and spaces (`RO12345678` = `12345678`);
  - the customer's own company and its contacts are no longer duplicates;
  - the phone is no longer checked: colleagues share the company phone, relatives a home phone.
- The messages never name the account found.

## 19.0.0.0.8 (2026-10-11)

- ANAF unavailable no longer blocks the checkout. The VAT number is looked up with a 5 s timeout
  (instead of 30 s) and the answer is read in three ways: company found (the address is filled in,
  as before), company not found (the number is refused, as before), service unavailable (the
  number is accepted as typed, the address is kept and the cart gets an internal note for the
  salesperson). Before, a down or slow ANAF refused every VAT number with "not valid according to
  ANAF".
- A personal numeric code (CNP) typed in the VAT field gets its own message, asking an individual
  to leave the field empty, instead of "not valid according to ANAF".

## 19.0.0.0.7 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.0.0.6 (2026-09-29)

- Own module icon, instead of the generic gears it had.

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
