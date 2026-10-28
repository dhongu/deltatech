# Changelog

## 19.0.1.3.4 (2026-10-28)

- Profit report: the purchase price is shown per product unit, like the quantity (it was per unit of the invoice line, so a line sold by the dozen showed the cost of a dozen next to a quantity in units). Changing it in the report converts it back to the unit of the line.
- Profit report: a line without a unit of measure keeps its quantity instead of an empty one.
- *Update Purchase Price* without *Price from delivery* converts the product cost to the unit of the invoice line.
- Profit report: new *Storable Products* filter (*Track Inventory* on the product), on by default.

## 19.0.1.3.3 (2026-10-22)

- The *selling below cost* check on customer invoices runs only when the sale price is set or changed, not when the cost is recomputed. Installing the module on a database with draft invoices below cost (the check mode defaults to *Block the sale*) stopped with "You can not sell below the purchase price."; it now installs, and a new line or a changed price below cost is still blocked.

## 19.0.1.3.2 (2026-10-22)

- Listed on Odoo Apps as *Sale Margin & Profit* (was *Sale Margin*). The technical name `deltatech_sale_margin` does not change.

## 19.0.1.3.1 (2026-10-22)

- Consultant sheet: points to *Sale Margin Report by Manufacturer* for the profit per
  manufacturer. Screenshots unchanged.

## 19.0.1.3.0 (2026-10-22)

- **Cost price on the customer invoices and the profit report (*Raport analiză profit*), moved
  here from `deltatech_sale_commission`**, which keeps only the commissions. A database with both
  modules keeps its records, ids and figures. A database with only this module gets the report
  (menu for *Show purchase price* and the sales managers) and the cost on the invoice lines; the
  cost of the old invoices is not computed at the update, run *Update Purchase Price* on them.
- The report accepts other sources of sales (`_extra_sources()`), added with UNION ALL and matched
  by column name with the invoices, so the extensions that add a column keep working. Their rows
  are read-only. Used by `deltatech_sale_margin_pos` for the POS orders without an invoice.
- *Update Purchase Price* and changing the cost in the report are allowed to whoever may change the
  report: the sales managers, and the commission managers with `deltatech_sale_commission`.
- Own module icon (`icon.svg` + `icon.png`), replacing the generic Deltatech one.
- Profit report action: no default grouping by salesperson in the context (it could not be removed from the search bar); it opens grouped by product.
- Margin report list: the product and the invoice are shown, so the lines can be told apart; the cost group gets its Romanian name.
- Consultant sheet, usage guide and screenshots: steps for the cost on the invoice, the profit report and the cost recalculation.

## 19.0.1.2.3 (2026-10-17)

- **Fix (MARGIN-002): the "No change price on sale order" group is enforced on
  the server.** It only made the price and the discount readonly in the order
  form, so the same user could still change them through RPC, another client or
  the discount wizard. Changing `price_unit` or `discount` on an existing line,
  directly or through the order lines, now raises an access error for members
  of the group, unless the new value is the one the pricelist computes.
  Automatic repricing ("Update prices", price recomputed on a product or
  quantity change), marketplace imports, the website cart and delivery, down
  payment and reward lines are still allowed. Creating a line with its own price
  (RMA, EDI and Excel imports) is not restricted.

## 19.0.1.2.2 (2026-10-10)

- Usage guide (`USAGE.md`) rebuilt from the consultant sheet, with numbered steps and screenshots; new `CONFIGURE.md`.

## 19.0.1.2.1 (2026-10-01)

- **Fix (MARGIN-001): the block now follows the same unit policy as the flag.**
  When the line unit and the product's base unit belong to different families
  (e.g. a product with `uom_id` = Units sold per kg), the native conversion
  inflates `purchase_price` (3.00 per Unit becomes 3000.00 per kg). The flag
  already stayed silent on such lines, but `check_sale_price()` (on `write` and
  on confirmation) and the onchange modal still compared the inflated cost, so
  in `block` mode a line with no "below cost" flag could not be saved. Both now
  skip the cost and margin comparison when `_margin_uom_comparable()` is False.
  Same-family units (Box 12 kg against kg) are still compared on the converted
  cost and still blocked. The "no price" check is unchanged.

## 19.0.1.2.0 (2026-08-20)

- **New: the reaction to a below-cost sale is configurable per company** —
  `res.company.sale_margin_check_mode`, in Settings > Sales > Pricing:

  - `block` (default, unchanged behaviour): the price cannot be saved and the
    order cannot be confirmed, unless the user belongs to the bypass groups;
  - `warn`: nothing is ever blocked. The line is flagged, the order shows a
    banner saying it can still be confirmed, and confirming it leaves a single
    note in the chatter;
  - `off`: no flag, no banner, no block.

  `warn` exists for businesses where selling below cost is a routine part of the
  trade — perishable goods, stock clearance, commercial gestures. Blocking there
  stops the daily work, while the actual need is to make it visible and let the
  seller decide. Existing databases keep the historical behaviour: the default is
  `block` and no migration changes it.

- **New: `sale.order.line.margin_below_limit`** — the line is flagged (orange row
  in the order lines) as soon as the seller leaves the price field, which is where
  the decision is made. The flag is readable by anyone: it says THAT the margin is
  under the limit, not what the cost is, so it does not leak the cost to sellers
  who are not allowed to see it. The figure stays on the native, group-restricted
  `margin_percent`.

- **New: unit guard on the comparison.** `purchase_price` is brought into the line
  unit by `sale_margin` / `sale_stock_margin` through
  `product_id.uom_id._compute_price(...)`. Odoo 19 removed the unit category, so
  that multiplies by the absolute factors without checking the family — the root
  of the kilogram hierarchy is the gram, so a cost of 3.00 per Unit becomes
  3000.00 per kg (measured, not assumed). A product whose `uom_id` is wrong would
  therefore report EVERY line as below cost and the warning would be dismissed as
  noise from day one. The comparison now stays silent when the line unit and the
  product's base unit belong to different families. New helper
  `uom.uom._dt_root_uom()`.

- **New: the margin settings are reachable from the interface.**
  `sale.margin_limit` and `sale.margin_limit_check_validate` existed but were only
  reachable through System Parameters, so in practice nobody configured them. They
  are now exposed in Settings > Sales, next to the reaction mode. `sale.margin_limit`
  doubles as the warning threshold: 0 reports only negative margins, a negative
  value tolerates a loss of up to that percentage, a positive value also reports
  thin but positive margins.

- The onchange modal ("Do not sell below the purchase price") now only appears in
  `block` mode. Where selling below cost is routine, a modal on every line ends up
  being dismissed reflexively without being read; the flagged row carries the same
  signal without interrupting.

- In `warn` mode `check_sale_price` stays silent on purpose. It runs on every
  `write` of a line, so the native `message_post` branch produced one chatter entry
  per keystroke on the price. The decision is now logged exactly once, on
  confirmation.

- `sale_stock_margin` is now a declared dependency. It was already pulled in by
  `auto_install`, but the cost used by the check comes from it (the real valuation
  of the delivery), so the behaviour should not depend on install order.

- **19 tests.** They run as an operator who is OUTSIDE the bypass groups, with a
  dedicated test asserting that: running them as root or admin proves nothing,
  since both belong to `group_sale_below_purchase_price` and the native check would
  not have blocked them either. Each mechanism was validated by sabotage — forcing
  the mode back to `block` breaks 4 tests, removing the chatter note or the banner
  wording breaks 2 more, disabling the unit guard breaks 1.

- Two pre-existing behaviours are now pinned down by tests, because they are easy
  to misread: in `block` mode the block fires from `sale.order.line.write`, so an
  order created through the API with inline lines and confirmed without touching a
  line is NOT blocked; blocking on confirmation requires
  `sale.margin_limit_check_validate`.
