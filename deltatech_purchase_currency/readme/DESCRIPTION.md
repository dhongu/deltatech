Bill a purchase order in another currency than the order currency, chosen through an
**Invoicing Journal** set on the order — the purchase counterpart of *Sale Invoice Currency*
(`deltatech_sale_currency`).

Typical case: a Romanian supplier quotes and confirms the order in EUR, but issues the vendor
bill in RON at the exchange rate of the bill date.

- **Invoicing Journal on the purchase order** (*Other Info* tab): the vendor bill is created in
  this journal and in its currency — the company currency when the journal has none. Without a
  journal the bill stays in the order currency, as in standard Odoo, so foreign suppliers are
  not affected.
- **Price conversion**: the order unit prices are converted to the bill currency at today's
  rate when the bill is created, and again at the rate of the *Bill Date* when it is set or
  changed. The price is first brought to the unit of measure of the bill line.
- **Auto-Complete** on a new vendor bill takes the order journal and currency.
- **Price matching flag** on the bill lines compares the bill price with the order price
  converted to the bill currency, so converted lines are not reported as price differences.
- **One extension point**, `purchase.order.line._get_invoice_price_unit()`, for another rate
  (for example the BNR rate plus a percentage agreed with the supplier).
