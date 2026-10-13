- Install the module. On install, the payment status is computed for existing orders.
- Enable the payment providers you use: **Accounting → Configuration → Online Payments → Payment
  Providers** (e.g. **Bank Transfer**). The **Confirm Payment** window offers only providers that are
  not disabled.
- For **electronic** providers (card, online payments), check the **Payment Journal** field in the
  **Configuration** tab of the provider. On the bank journal, under **Incoming Payments**, set the
  **Outstanding Receipts** account of the provider's line to an account for amounts in course of
  settlement (a dedicated analytic account per provider is recommended), so the money not yet settled
  does not appear as available in the bank.
- Optionally, in **Sales → Configuration → Settings**, enable automatic invoicing, so an order paid
  through an **electronic** provider (or confirmed with **Confirm** on **Bank Transfer**) is invoiced
  automatically.
- Set the down payment account: **Accounting → Configuration → Settings → Default Accounts →
  Down Payment Account** (customer advances account), otherwise the down payment invoice line goes to
  the product income account.
- In the order list, the **Payment Status** column is visible by default; **Payment Provider** is added
  from the optional columns selector.
