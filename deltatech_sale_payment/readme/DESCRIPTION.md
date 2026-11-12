Sales staff need to see from the order whether the customer has paid. This module adds the collected amount and a payment status to sales orders and lets a user record a payment from the order.

- **Payment on the order**: The order form shows *Payment*, the amount collected, next to the payment provider, followed by *Payment Status*.
- **Seven statuses**: Orders get one of *Without*, *Initiated*, *Pending*, *Authorized*, *Partial*, *Done* or *Cancelled*. The quotation and order lists show the status by default, and the search view has a filter for each status except *Partial*.
- **Confirm Payment**: The *Confirm Payment* action of the order opens a window that asks for the provider, the payment method and the amount. The window starts from the last transaction of the order when that one is pending or authorized.
- **Confirm or Add**: The *Confirm* button marks the transaction as done, so the amount counts as collected on the order. *Add* only records a pending transaction.
- **Checks**: The window offers only providers that are not disabled and refuses a negative amount.

It depends on *Sales* and `payment`. The *Confirm Payment* action has no group of its own, and salespeople can read the payment providers.
