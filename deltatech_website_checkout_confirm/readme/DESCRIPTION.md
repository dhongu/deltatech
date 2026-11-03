In standard Odoo eCommerce, a quotation paid by wire transfer or cash on delivery stays a quotation
after checkout: the transaction is only `pending`, so the order is confirmed later, by hand or when
the payment is received. This module confirms the order as soon as the customer reaches the
order confirmation page (`/shop/confirmation`) at the end of checkout.

There is no extra page or button: the module works on the standard confirmation route of
`website_sale`.

**Automatic confirmation at the end of checkout**: when the customer lands on the confirmation page,
the last order of the session is confirmed (`Sales Order` state), so the delivery and the rest of the
sales flow start right away.

**Offline payment methods included**: a `pending` transaction on a provider without online processing
(wire transfer, cash on delivery) is enough to confirm the order. Online providers still need a
`Confirmed` or `Authorized` transaction.

**Same checks as the standard payment flow**: the order is confirmed only if it is still a quotation,
no online signature is pending, and the qualifying transactions, linked only to this order, cover
the amount required for confirmation (the full amount or the prepayment percentage set on the
quotation). Reloading the page on an already confirmed order does nothing.

## Limitations

- A transaction that pays several orders at once is not taken into account, as in the standard
  post-processing.
