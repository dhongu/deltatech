Limits the delivery methods and the payment providers offered in the eCommerce checkout by the delivery method chosen,
the value and weight of the order and the tags of the customer.

## Features

- **Payment providers by delivery method**: a delivery method can list the payment providers allowed with it, for
  example cash on delivery only with the courier. On the payment step the customer sees only those providers. A
  delivery method without a list allows all of them.
- **Value limit of a payment provider**: above this order total (taxes included) the provider is no longer offered.
- **Weight limits of a delivery method**: the method is offered only when the estimated weight of the cart is between
  its minimum and maximum. An empty limit is not checked.
- **Restrictions by customer tags**: a delivery method or a payment provider can be hidden from the customers that have
  one of its tags. The tags of the customer's company (the commercial partner) are read for both.
- **Check when paying**: the payment provider is checked again when the transaction is created, so a provider that is
  not allowed for the order is refused, also in the express checkout. The express checkout hides the delivery methods
  whose allowed providers have no express checkout.
- **Preferred payment provider**: the *Payment Provider* set on the customer's company preselects its payment method on
  the payment step, when that provider is allowed for the order.
- **Delivery method logo**: the *Logo* of a delivery method is shown before its name in the shop checkout.

## Configuration

- **Website > Configuration > eCommerce > Delivery Methods**, on a delivery method:
  - *Weight limits*, on its own row under the price, in the weight unit of the database;
  - tab *Payment Acquirer*: *Payments Provider Allowed* and *Restrict for partners with label*;
  - *Logo*, the image at the top right of the form.
- **Website > Configuration > eCommerce > Payment Providers**, on a provider, tab *Restrictions*, under *Maximum Amount*: *Value Limit* and the tags.
- On the contact form, tab *Sales & Purchase*: *Payment Provider*, the preferred provider of the customer.
