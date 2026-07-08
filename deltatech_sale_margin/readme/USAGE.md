1. Assign users to the technical security groups (Settings > Users & Companies > Users, or Settings > Technical > Security > Groups) that control margin behaviour on sale orders and customer invoices:
   - **Show purchase price on sale order lines and customer invoice** – lets a user see the margin and purchase price fields; without it these are hidden.
   - **No change price on sale order** – makes the price/discount fields on sale order lines read-only for that user.
   - **Sell below the purchase price** – lets a user confirm/save a line whose sale price is below the purchase price without being blocked.
   - **Sell below margin limit** – lets a user confirm an order that is below the configured margin limit.
2. If a user without the "sell below purchase price/margin" rights sets a price under cost, a warning message is shown on the sale order header; if they lack the right entirely, the system blocks the action with an error instead of just a warning.
3. Optionally set the system parameters (Settings > Technical > Parameters > System Parameters):
   - `sale.check_price_website` – enables the price check for orders coming from the website.
   - `sale.margin_limit_check_validate` – if set, the margin/purchase price check is only enforced when the order is confirmed, so users without the right can still create and save draft orders below margin.
