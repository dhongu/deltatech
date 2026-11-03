## 19.0.2.1.8 (2026-11-03)

- Description rewritten to match the code: value limit of a payment provider, weight limits of a
  delivery method, which customer tags are read, where each setting is. The obsolete "work in progress"
  note is removed. Summary typo fixed.
- Consultant sheet (FISA_CONSULTANT.md), USAGE.md and screenshots in Romanian and English
  (`tests/test_screenshots.py`), including the delivery and payment steps of the shop checkout.
  *Weight limits* moved to its own row of the delivery method form (it was squeezed next to the
  *Free if order amount is above* checkbox) and shows the weight unit; Romanian translations updated.

## 19.0.2.1.7 (2026-10-16)

- Removed the inactive frontend script and the `data-acquirer-allowed-ids` attribute on the delivery methods:
  in Odoo 19 the payment methods are on `/shop/payment`, after the delivery step, and are already filtered
  on the server by the allowed providers of the selected carrier.

## 19.0.2.1.6 (2026-10-09)

- Apps Store banner (banner.json).

## 19.0.2.1.5 (2026-09-30)

- New module icon in the flat style of the other modules; it replaces the old one.
