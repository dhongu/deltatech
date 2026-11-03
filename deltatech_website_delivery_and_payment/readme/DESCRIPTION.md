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
  one of its tags. For delivery methods the tags of the customer's company are read; for payment providers, the tags of
  the customer on the order.

## Configuration

- **Website > Configuration > eCommerce > Delivery Methods**, on a delivery method:
  - *Weight limits*, next to the price;
  - tab *Payment Acquirer*: *Payments Provider Allowed* and *Restrict for partners with label*.
- **Website > Configuration > eCommerce > Payment Providers**, on a provider, group *Restrictions*: *Value Limit* and the tags.

The module also adds a *Logo* to the delivery method form and a *Payment Provider* field to the *Sales & Purchase* tab
of the contact form. They are stored for other modules and reports; this module does not use them in the checkout.
