1. Go to *Website > Configuration > Settings*, section **eCommerce**. Check **Prevent Sale of Zero
   Priced Product**: the module fields appear next to it. Leave **Cost Price Includes Tax** unchecked
   when the product cost is kept without taxes (on a website showing prices without taxes this option
   does not remove the tax from the cost: keep the cost without taxes and leave it unchecked), set
   **Cost Price Margin %** (e.g. 10) and save.

   ![Website settings: Prevent Sale of Zero Priced Product checked (1), Cost Price Includes Tax unchecked (2) and Cost Price Margin % set to 10 (3)](static/description/en/01_setari_pret_cost.png)

2. On the product (*Website > eCommerce > Products*, tab **General Information**), the **Sales Price**
   is compared with the **Cost** plus the margin. Here 42.00 is below 40.00 + 10% = 44.00, so the
   product cannot be bought online. The compared price is the website price, after the website
   pricelist.

   ![Product form: Sales Price 42.00 (1) and Cost 40.00 (2)](static/description/en/02_produs_pret_cost.png)

3. In the shop, the product below the threshold has no cart button in the product list, while the
   other one is sold as usual.

   ![Shop category: the product below the threshold (1) without cart button, the other one (2) with Add to Cart](static/description/en/03_magazin_lista_produse.png)

4. On its product page, the price and **Add to Cart** are replaced by the **Contact Us** button
   (the **Button URL** from the settings).

   ![Product page of the blocked product: only the Contact Us button (1)](static/description/en/04_produs_blocat_magazin.png)

5. A product above the threshold shows its price and **Add to Cart** as usual.

   ![Product page of an allowed product: the price (1) and Add to Cart (2)](static/description/en/05_produs_permis_magazin.png)

Check the shop as a visitor (private window): users of the *Settings* group can still add a blocked
product to the cart.
