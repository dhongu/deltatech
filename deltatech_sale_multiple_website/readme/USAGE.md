1. Open the product (*Website > eCommerce > Products > Products*), tab **Sales**. In the **Quantity** group, set
   **Qty Multiple** (for example 50) and **Qty Minim** (for example 100). Keep **Website Check Quantity**
   ticked to apply the rules only to website orders, or untick it to apply them to backend quotations
   too. Save the product.

   ![Product form, Sales tab: Qty Multiple 50.00 (1), Qty Minim 100.00 (2) and Website Check Quantity (3)](static/description/en/01_reguli_cantitate_produs.png)

2. On the product page of the shop, the restrictions are shown under the add to cart button
   (**Min: 100**, **Multiple of: 50**); the info icon explains each rule. For products with variants,
   the restrictions follow the selected variant.

   ![The product page in the shop: the restrictions Min: 100 and Multiple of: 50 (1), with the explanation of the multiple open](static/description/en/02_restrictii_pagina_produs.png)

3. In the cart, the quantity is rounded up to the minimum and then to the next multiple: 130 units
   requested become 150. The rules are recalled under the product name.

   ![The cart: the rules Min: 100.00 and x50.00 under the product (1) and the quantity 150 (2), rounded up from 130](static/description/en/03_cos_cantitate_rotunjita.png)

   When the available stock caps the quantity, the cart keeps the greatest quantity that fits in stock
   and still respects both rules; below the minimum, the product is not added.

4. With **Website Check Quantity** ticked, a quotation entered in the backend keeps the typed quantity
   (130 stays 130). Untick it to round backend quotations as well. Orders coming from the website keep
   the rules when edited in the backend.

   ![A backend quotation: the line keeps Quantity 130.00, because the rule applies only to the website](static/description/en/04_oferta_backend_fara_regula.png)

**Website Check Quantity** is ticked by default, so after installation every product applies its rules
only on the website. For products with several variants, set the rules on each variant.
