# Changelog

## 19.0.1.6.0 (2026-09-24)

Fixes from the consultant sheet audit:

- Rights: the commission and cost wizards (`commission.compute`,
  `commission.update.purchase.price`) and their *Actions* entries are limited to
  *Commission Manager*. **Apply** now works for a Commission Manager without an
  invoicing right: the wizard checks the group and writes the commission with
  sudo. Writes on `sale.margin.report` go through the access check, so a
  *Commission Viewer* can no longer mark a commission paid or change it; the
  *Set Paid* button is shown to managers only.
- A write on the margin report no longer puts the product cost on a line whose
  cost is 0 (it did so even on *Set Paid*).
- A credit note without a return of goods has cost 0. It used to get the product
  cost, or the invoice cost when made by reversal (`purchase_price` was copied),
  and could produce a positive profit and commission. The update wizard and the
  daily cron no longer bring the product cost back on such a line.
- Changing *Salesperson commission compute* rebuilds the report after the setting
  is saved; the onchange rebuilt it with the old value.
- `commission.users`: the journal is required (sales journals only; the domain
  used the `sale_refund` type, gone in Odoo 19) and (salesperson, journal,
  company) is unique, so the report lines are no longer duplicated. The
  migration fills the journal where the company has a single sales journal and
  logs the rows without journal and the duplicates, to be cleaned up by hand.
- Invoices *In Payment* count as paid for the commission, and the wizards opened
  without a selection list the paid lines without commission (the default filter
  used a non-existent invoice state); the *Paid* filter includes them too.
  `days_for_commission = 0` now means "paid at
  the latest on the due date"; only a missing or empty parameter disables the
  condition. A non-numeric or negative value is refused.
- Removed the unused `sale.commission.condition` model.
- The *Commission* list no longer shows *Due Date* twice.

## 19.0.1.5.2 (2026-09-23)

- Translatable strings in code use `self.env._()` instead of `_()`, the Odoo 19
  convention (pylint-odoo `prefer-env-translation`). The translated messages are
  unchanged.

## 19.0.1.5.0 (2026-08-20)

- `account.move.line._check_sale_price` now honours the company policy
  `res.company.sale_margin_check_mode` from `deltatech_sale_margin`. It used to
  raise unconditionally, which meant a company allowed to sell below cost would
  pass the sale order and then hit the wall at invoicing — once the goods were
  already delivered. The constraint still blocks in `block` mode, which stays the
  default.
