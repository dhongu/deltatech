Cleans the address form of the website checkout and of the customer portal and stops a logged-in customer from
registering a tax code or an e-mail address that already belongs to another customer. It also keeps the website price
display setting (with or without taxes) from being reset in the background.

The format of the tax code is checked by Odoo itself (`base_vat`). The Romanian checks of the tax code (ANAF look-up,
personal numeric code, struck-off company) are in `l10n_ro_website_anaf` (l10n-romania): this module stays
country-neutral.

## Features

- **Trimmed values**: the spaces before and after the tax code, the e-mail and the phone typed in the address form are
  removed.
- **Duplicate tax code blocked**: a logged-in customer cannot use a tax code that another customer already has. The
  codes are compared without their country prefix and spaces, so `RO 12 34 56 07`, `ro12345607` and `12345607` are the
  same code.
- **Duplicate e-mail blocked**: a logged-in customer cannot use an e-mail address of another account; the message asks
  to log in with that account or to use another address.
- **Messages that say what to do**: for a tax code already in use, the customer is asked to get access from a colleague
  who has an account, to send an access request from the `/b2b` page (with `deltatech_b2b_portal`) or to contact the
  shop. The messages never name the account found.
- **No false duplicates**: the customer's own company and its contacts are not duplicates, and the phone is not checked,
  since colleagues share the company phone and relatives a home phone.
- **Guest checkout unchanged**: the duplicate checks run only for logged-in customers. For an anonymous visitor the
  message would tell anyone that an e-mail address or a tax code belongs to an existing customer.
- **No second company at checkout**: a person who fills in a company name and a tax code in the billing address buys
  for that company; Odoo 20 creates the company as a partner with this address and tax code and makes the person its
  contact. The module lets this happen only for a tax code no other customer has: a visitor (not logged in) who types
  the tax code of a customer keeps it on their own address, no second company with the same tax code is created and the
  visitor is not attached to the existing company, so they never see its documents.
- **Price display kept**: the website setting *Display Product Prices* (tax included or excluded) keeps its saved value
  when Odoo recomputes it, for example after the address of the company's own partner is updated by an ANAF sync.
  Without the module, Odoo puts it back to tax excluded.

## Update from a version before 19.0.0.2.0

The ANAF checks moved to `l10n_ro_website_anaf`. A database that had them (`l10n_ro_partner_create_by_vat` installed)
gets `l10n_ro_website_anaf` installed with the update, when l10n-romania is on the addons path; otherwise the log says
to add it.
