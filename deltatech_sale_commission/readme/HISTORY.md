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
- Cost of a credit note line without a return of goods: a reversal of the invoice
  (same product, unit and price, for all or part of the quantity) keeps the unit
  cost of the invoice line, so the pair nets to a zero profit, as before. A line
  whose price or discount was changed (a price reduction), or a credit note that
  reverses no invoice, has cost 0. It used to get the product cost, or keep the
  copied invoice cost after the price was edited, and could produce a positive
  profit and commission. The cost is recomputed when the price or the discount
  changes, and the update wizard and the daily cron follow the same rule.
- Changing *Salesperson commission compute* rebuilds the report after the setting
  is saved; the onchange rebuilt it with the old value.
- `commission.users`: the journal is required (sales journals only; the domain
  used the `sale_refund` type, gone in Odoo 19) and (salesperson, journal,
  company) is unique, so the report lines are no longer duplicated. The
  migration fills the journal where the company has a single sales journal, one
  row per salesperson and only if the salesperson has no row on that journal yet
  (so it creates no duplicates), and logs the rows left without journal and the
  duplicates with different rates, to be cleaned up by hand; exact duplicates are
  deleted. The margin report takes at most one rate row per invoice line (the
  oldest), so a duplicate left in the data can no longer double the sale, cost,
  profit and commission, and the ORM refuses a new duplicate even where the
  unique index could not be created yet. Before upgrading a production
  database, run `scripts/sale_commission_precheck_1_6_0.py` (read-only) to see
  what changes for the client.
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
