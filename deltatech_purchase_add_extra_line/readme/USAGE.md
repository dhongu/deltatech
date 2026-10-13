Before you start, configure the main product as described in *Configuration*.

The extra line works only while the order is a **Request for Quotation** or a
**Quotation Sent**. After confirmation it is no longer generated or synchronized.

**Step 1 - Configure the main product**

Go to **Purchase → Products → Products**, open the main product and select the
**Purchase** tab, group **Extra Line**. Fill in the extra product, the percentage
and the quantity multiplier, then save.

In the example, "Motor electric 7,5 kW" has "Transport și manipulare" attached,
with **Extra Percent = 5** and **Extra Quantity = 1**.

![Extra line configuration on the main product](/extra_line_product_config.png)

**Step 2 - Create the request for quotation: the extra line appears automatically**

Go to **Purchase → Orders → Requests for Quotation → New**, choose the vendor and
add the main product with the quantity you need. The extra line is inserted right
below the main line.

- **Quantity** = main line quantity × **Extra Quantity** (5 motors → 5 transports).
- **Unit price** = main line unit price × **Extra Percent** / 100 (5% of 2,400.00
  = 120.00).

The line is also generated when lines are saved through import or API, and when
the request is sent by email or printed.

![Request for quotation with the automatically generated extra line](/extra_line_rfq_generated.png)

**Step 3 - Quantity stays in sync**

Change the quantity of the main line. The extra line follows it, always multiplied
by **Extra Quantity**, and the subtotal grows accordingly. The quantity and unit of
measure of the extra line are read-only; only its price can be edited.

![Extra line quantity follows the main line](/extra_line_qty_synced.png)

**Step 4 - Negotiate the price manually**

If the vendor accepts a fixed price, edit the **Unit Price** directly on the extra
line and save. The manual price is kept: it is not overwritten when you change the
quantity or the price of the main line. In the example the transport was negotiated
at 80.00 instead of 120.00.

![Manual price kept on the extra line](/extra_line_manual_price.png)

**Step 5 - Go back to the calculated price**

Delete the extra line (trash icon). It is regenerated immediately with the price
calculated from the percentage (120.00 in the example). This is the normal
regeneration mechanism, not a failed deletion.

![Extra line regenerated with the calculated price](/extra_line_price_restored.png)

If you delete the **main line**, the associated extra line is deleted too.

**Step 6 - Confirm the order**

Click **Confirm Order**. The extra line becomes a normal purchase order line, with
the quantity and price you set. It is then picked up by the receipt (if the extra
product is storable) and by the vendor bill. From this point the extra line is no
longer synchronized.

![Confirmed purchase order with the extra line](/extra_line_order_confirmed.png)
