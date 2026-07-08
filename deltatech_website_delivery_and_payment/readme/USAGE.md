This module adds restriction rules between delivery methods, payment providers, and customers on the website checkout.

1. On a Delivery Method (Inventory > Configuration > Delivery Methods), open the new **Payment Acquirer** tab to:
   - restrict which Payment Providers are allowed for that carrier (**Payments Provider Allowed**);
   - restrict the carrier to customers whose contact has a given tag (**Restrict for partners with label**).
   - Set **Weight limits** (Min/Max) on the carrier so it is only offered when the order's estimated weight falls in that range.
2. On a Payment Provider (Website > Configuration > Payment Providers), the **Restrictions** group lets you:
   - set a **Value Limit**, above which the provider is no longer offered;
   - restrict the provider to customers whose contact has a given tag (**Restrict for partners with label**, res.partner.category tags).
3. On a Contact's form (Sales & Purchase tab), you can set a preferred **Payment Provider** for that customer.
4. At checkout, delivery methods and payment providers that don't meet the weight, value, tag, or allowed-provider restrictions are automatically hidden from the customer.
