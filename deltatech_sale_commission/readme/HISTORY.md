# Changelog

## 20.0.1.6.3 (2026-10-15)

Port of the 19.0 1.6.x series (19.0.1.6.0 and 19.0.1.6.3; 19.0.1.6.1 and 19.0.1.6.2 were
already ported as 20.0.1.5.3 and 20.0.1.5.5). Differences from 19.0:

- Rights are rows of `security/ir.access.csv`: the two wizards are granted to *Commission
  Manager* instead of *Internal User*, and the rows of `sale.commission.condition` are gone.
- The pre-migration runs as `migrations/20.0.1.6.0`, so a database at 20.0.1.5.x gets it on
  upgrade; it is idempotent, a database that already ran it on 19.0 is left unchanged.
- The precheck script `scripts/sale_commission_precheck_1_6_0.py` reads the parameters with
  `get_str`.
- Usage guide (`USAGE.md`) rebuilt from the consultant sheet, with numbered steps and
  screenshots; new `CONFIGURE.md`.

Fixes from the consultant sheet audit (port of 19.0.1.6.0):

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
  changes; because `Cost Price` is a computed field, a cost typed in by hand on a
  **draft** line is lost when the price is changed afterwards, as it already was
  when the product was changed. The update wizard and the daily cron read the
  same rule (`account.move.line._purchase_price_from_document`) but do not write
  the same way, on purpose: the wizard is run by hand and *resets* the cost, 0
  included, which is how a credit note wrongly costed in the past gets corrected;
  the cron runs unattended over a whole week of invoicing and only *fills in* a
  missing cost, so that it can never silently undo a cost set by hand.
- Careful with **Update purchase price → for all** after the upgrade: the rule
  for the cost of a credit note changed, so running it over the whole history
  rewrites the cost of the old credit notes, and with it the profit already
  reported for those months. It is the correction the audit asked for, but it
  changes figures the client has already seen — agree on it first.
- Changing *Salesperson commission compute* rebuilds the report after the setting
  is saved; the onchange rebuilt it with the old value.
- `commission.users`: the journal is required (sales journals only; the domain
  used the `sale_refund` type, gone since Odoo 19) and (salesperson, journal,
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
- The margin report also matches the rate on the **company**, which it did not do
  before: a `commission.users` row filed under a company other than the one of
  its journal used to apply and would now be ignored, taking a salesperson's
  commission away with nothing on screen to say why. The migration moves such a
  row onto the company of its journal, so nothing changes for it, and reports the
  ones it can not move (the salesperson already has a row there). A new row can
  no longer be created with the wrong company, by the form or by an import.
- Invoices *In Payment* count as paid for the commission, and the wizards opened
  without a selection list the paid lines without commission (the default filter
  used a non-existent invoice state); the *Paid* filter includes them too.
  `days_for_commission = 0` now means "paid at
  the latest on the due date"; only a missing or empty parameter disables the
  condition. A non-numeric or negative value is refused. Because that default
  selection now really returns something — it used to be empty on every database
  — *Compute commission* writes the lines grouped by the value it sets, one write
  per distinct commission instead of one per line.
- Removed the unused `sale.commission.condition` model.
- The *Commission* list no longer shows *Due Date* twice.

## 20.0.1.5.5 (2026-10-04)

- COMMISSION-003 (security): the commission rates (`commission.users`) had no company rule, so a Commission Manager allowed only in company A could read, change, delete or create the rates of company B (salesperson, manager and director rates). A multi-company restriction now limits the rates to the allowed companies, and moving a rate to another company requires access to that company.
- Port of 19.0.1.6.2 (dhongu/deltatech#3116). In 20 the company rule is a global row (no group, `crud`) of `security/ir.access.csv` instead of an `ir.rule` in the `noupdate` `security/security.xml`, so it is also updated on module upgrade.

## 20.0.1.5.4 (2026-10-01)

- [FIX] in "block" mode, the invoice of a confirmed sale order is no longer refused with "You can not sell below the purchase price." when the line is invoiced at the price of its order line: that price was already judged on the order, possibly by a seller allowed to sell below cost. A price changed on the invoice, and invoice lines without an order, are still checked.

## 20.0.1.5.3 (2026-10-01)

- Margin report: the quantity of an invoice line in another unit than the product
  unit is converted with the right ratio. Two dozen of a product sold by the unit
  now show as 24 units (they showed as 1/6). Refunds keep their sign.

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
