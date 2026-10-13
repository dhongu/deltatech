Before you start, set up the extra product on the main product as described in *Configuration*.

## Add an extra line automatically to a sales order

**Step 1 — Set up the main product**

Go to **Sales → Products → Products**, open the main product and switch to the **Sales** tab. In the **Extra Line** group, fill in the extra product, the percentage and the quantity multiplier, then save. In the example, the boiler has an installation service attached, with **Extra Percent = 10** (installation costs 10% of the boiler price) and **Extra Quantity = 1** (one installation for each boiler sold).

![Extra Line group on the main product form](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_add_extra_line/extra_line_product_setup.png)

**Step 2 — Create the order: the extra line appears by itself**

Go to **Sales → Orders → Quotations → New**, choose the customer and add the main product with the quantity you need. As soon as you leave the line, a second line with the extra product is inserted right below the main one.

- Extra line **quantity** = main line quantity × **Extra Quantity** (2 boilers → 2 installations).
- Extra line **unit price** = main line price × **Extra Percent** / 100 (450.00, i.e. 10% of 4,500.00).

![Quotation with the automatically generated extra line](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_add_extra_line/extra_line_order_auto.png)

The line shows up immediately in the form and is stored when you save the order.

**Step 3 — Use the quantity multiplier**

The extra line quantity always follows the main line, multiplied by **Extra Quantity**. In the example, a case of beer has **Extra Quantity = 6** (six packagings per case) and **Extra Percent = 0**.

- Selling **10 cases** gives **60** packagings on the extra line.
- With **Extra Percent = 0** the extra product keeps its own price (here 0.50), taken from the customer's pricelist.
- Whenever you change the main quantity, the extra quantity is recalculated in the same ratio.

![Extra line quantity follows the main line](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_add_extra_line/extra_line_quantity_multiplier.png)

**Step 4 — Negotiate a price manually on the extra line**

When the calculated price does not fit, change the **unit price directly on the extra line** and save. The price you typed is kept: it is no longer overwritten when you change the quantity or the price of the main line. In the example the installation was negotiated at **300.00** instead of 450.00, and the boiler quantity was then raised to 3. The price stays at 300.00 while the extra quantity is updated to 3.

This works with a percentage as well as with **Extra Percent = 0**.

![Manual price kept on the extra line](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_add_extra_line/extra_line_manual_price.png)

**Step 5 — Go back to the calculated price**

If the negotiated price is no longer valid, **delete the extra line** (trash icon at the end of the line), then change anything on the main line. The extra line is generated again with the price calculated from the percentage (450.00 in the example, instead of the negotiated 300.00).

![Extra line regenerated with the calculated price](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_add_extra_line/extra_line_price_regenerated.png)

If you delete the **main line**, the associated extra line is deleted automatically, so no orphan line is left on the order.

**Step 6 — Invoice the order**

Confirm the order and click **Create Invoice**. The extra line reaches the invoice as a normal line, with the product, quantity and price from the order. On the draft invoice, check that:

- the extra line is present, with the price from the order and the matching amount (900.00 for 2 installations);
- the account of each line comes from the **product category**, and the tax is the one set on the extra product.

![Invoice with the extra line taken over from the order](https://apps.odoocdn.com/apps/assets/19.0/deltatech_sale_add_extra_line/extra_line_invoice.png)

## Good to know

- **Online shop:** the extra line is generated automatically in the cart. The customer cannot remove it: if the quantity is set to 0, it is regenerated at the next cart update while the main product stays in the cart.
- **Point of Sale** (optional module): only the quantity is synchronized. The **Extra Percent** is not applied, so set the extra product to the desired price and leave the percentage at 0.
- **Orders created in other ways** (file import, API, quotation templates, other modules) do not receive the extra line automatically.
