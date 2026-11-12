The sale price is computed as **last purchase price × (1 + trade markup / 100)**, without taxes.

1. Go to **Settings → Purchase**, section **Products**, and choose the options:

   - **Update product price**: at receipt, the vendor price on the product's *Purchase* tab is
     replaced with the purchase order price (vendor lines without a minimum quantity above 1 and
     without a validity period);
   - **Update list price**: the sales price is recomputed from the last purchase price and the
     trade markup: at receipt, when the markup is set on several products, and when you change the
     markup or the last purchase price on the product;
   - **Add supplier to product**: the vendor and its price are added to the product when a purchase
     order is confirmed;
   - **Force supplier price at PO and bill confirmation**: the vendor price is also updated when the
     purchase order is confirmed and when the vendor bill is posted.

   ![Purchase settings, Products section: Update product price and Update list price are checked and marked 1 and 2](static/description/en/01_setari_achizitii.png)

2. Open a product (**Sales → Products → Products**, *General Information* tab). Set the **Trade
   Markup** (30.00 means 30%). The **Last Purchase Price** is shown in green when it is not above the
   **Cost**, and in red when it is. With **Update list price** enabled: 100.00 × 1.30 = **130.00**.

   ![Product form: Last Purchase Price 100.00, Trade Markup 30.00, Sales Price 130.00 lei](static/description/en/02_produs_adaos.png)

3. To set the markup on several products, select them in the list view and use **Actions → Set
   Trade Markup**. Check **Selected Line** to apply it to the selected products; unchecked, choose a
   **Vendor** and the markup applies to all the products of that vendor. Click **Set**.

   ![Products list with two products selected and the Set Trade Markup dialog: Selected Line checked, Trade Markup 30.00 and the Set button](static/description/en/03_wizard_adaos.png)

4. Confirm a purchase order and validate its receipt. For each product received on the order, the
   **Last Purchase Price** becomes the order unit price, converted to the company currency and to the
   product unit of measure. Receipts without a purchase order do not change prices.

   ![Validated receipt from the vendor, 20.00 units received](static/description/en/04_receptie_validata.png)

5. After the receipt at 110.00, the product shows **Last Purchase Price** 110.00 (in red, above the
   cost), **Trade Markup** 30.00 and **Sales Price** 110.00 × 1.30 = **143.00**. The **Cost** is not
   changed by the module: it comes from the stock valuation. A product without markup keeps its
   sales price.

   ![Product after the receipt: Last Purchase Price 110.00, Trade Markup 30.00, Sales Price 143.00 lei](static/description/en/05_produs_dupa_receptie.png)

6. With **Update list price** disabled, the sales price is set by hand and the markup follows it:
   changing the last purchase price (or the sales price) recomputes the markup. For a sales price of
   13.00 and a corrected purchase price of 12.50, the markup becomes (13.00 − 12.50) / 12.50 × 100 =
   **4.00**. A markup typed by hand is kept.

   ![Product with Update list price disabled: Last Purchase Price 12.50, Trade Markup recomputed to 4.00, Sales Price unchanged at 13.00 lei](static/description/en/06_adaos_recalculat.png)

The rounding of the computed sales price is set by the system parameter `sale.list_price_round`
(number of decimals, default 2). A pricelist rule can use **Last Purchase Price** as its base price.
