This is a pure behind-the-scenes fix, there is nothing to configure. Once installed, it automatically changes how the **Invoice Status** of a sale order is computed for consumable/storable products combined with services:

- If a sale order has both products and services, and no products have been delivered yet, the order's invoice status stays "Nothing to Invoice" instead of switching to "To Invoice" just because a service line is invoiceable.
- If the order only contains service lines, the invoice status is set to "To Invoice" as usual.

No user action is required — the effect is visible on the **Invoice Status** field of sale orders and order lines once delivery is confirmed or products are shipped.
