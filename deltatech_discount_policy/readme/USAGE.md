1. Go to **Sales > Configuration > Pricelists**, open a pricelist and set the **Discount Policy** field:
   - **Discount included in the price** — the sales order line shows the final discounted unit price and the Discount % is left at 0.
   - **Show public price & discount to the customer** — the sales order line shows the original (public) unit price and the discount percentage is displayed explicitly, even when the pricelist rule uses a fixed price.
2. No further configuration is needed: once the policy is set, sales order lines using that pricelist automatically compute the correct base price/discount, including for fixed-price pricelist rules.
