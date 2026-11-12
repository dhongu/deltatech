Sales staff need to see from the order whether the customer has paid. This module adds the collected amount and a payment status to sales orders and lets a salesperson record a payment.

- **Payment on the order**: The order form shows *Payment*, the amount collected, with the *Provider* and *Payment Status*.
- **Seven statuses**: Orders get one of *Without*, *Initiated*, *Pending*, *Authorized*, *Partial*, *Done* or *Cancelled*, shown by default in the quotation and order lists, with filters and grouping.
- **Confirm Payment**: An action of the order opens a window starting from the latest draft or pending transaction, or from the amount left to collect, and asks for provider, method, amount and *Payment Date*.
- **Confirm or Add**: The *Confirm* button marks the transaction done and notes the entered date on the order; Odoo can then confirm the quotation. *Add* only records a pending transaction.
- **Safeguards**: The window needs write access to the order, not Invoicing rights, and refuses a negative amount, an authorized payment, another order's transaction, another company's provider, and a method the provider does not offer.

It depends on Sales, `payment` and `account_payment`; the action is for Sales users. A provider whose journal has no payment method line (such as wire transfer) gets no accounting payment; the accountant records it.
