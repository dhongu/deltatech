Enable the pricelists first: *Sales > Configuration > Settings*, section **Pricing**, tick
**Pricelists** and save.

**Add rules for many products**

1. Go to *Sales > Products > Pricelists* and open a pricelist. The header has the **Add Rules**
   and **Apply Formula** buttons (**Apply Formula** only when the pricelist has rules).

   ![Pricelist form with the Add Rules and Apply Formula buttons highlighted in the header and two fixed price rules of a laptop in the Sales Prices tab](static/description/en/01_formular_lista_preturi.png)

2. Click **Add Rules**. Choose **Apply On** (products, product variants or product categories) and
   add the products. To take all the products of a category and of its subcategories, select it in
   **Add Products of Categories**. Set the **Min. Quantity**, the **Validity Period** and the price
   computation, then choose what to do with a rule that already exists for the same product,
   minimum quantity and validity period: keep it, update it or add a new rule.

   ![Add Pricelist Rules wizard with five peripherals selected, a Formula based on the Sales Price with 10% discount, rounding to 1.00 and an extra fee of -0.01, and Keep the existing rule selected](static/description/en/02_asistent_adauga_reguli.png)

3. Click **Add Rules**. A message shows how many rules were added, updated or kept, and the rules
   open in a list.

   ![Price Rules list with the message 5 rules added, 0 rules updated, 0 existing rules kept, and one rule for each peripheral with the same 10 % discount on sales price - 0.01 rebate](static/description/en/03_reguli_adaugate.png)

4. You can also start from the products: in *Sales > Products > Products*, select the products and
   use *Actions > Add to Pricelist*. The wizard opens with the selected products; choose the
   pricelist.

   ![Product list with three products selected and the Actions menu open on Add to Pricelist](static/description/en/04_actiune_din_produse.png)

**Apply the same formula to many rules**

1. On the pricelist form, click **Apply Formula** to change all its rules, or select some rules in
   a list of pricelist rules and use *Actions > Apply Formula*. Remove from the list the rules you
   do not want to change.
2. Tick what to change: **Change the Price Computation**, **Change the Min. Quantity** and/or
   **Change the Validity Period**, and set the new values. What is not ticked stays as it is on
   each rule.

   ![Apply Formula wizard on the 7 rules of the pricelist, with Change the Price Computation ticked and a Formula based on the Cost with 35% markup, rounding to 1.00 and an extra fee of -0.01](static/description/en/05_asistent_aplica_formula.png)

3. Click **Apply**. All the selected rules get the new computation; the values of the old price
   type (e.g. the fixed price) are cleared, as on the standard rule form.

   ![Pricelist form after the change: the message 7 rules changed and all the rules in the Sales Prices tab with 35 % markup on product cost - 0.01 rebate, the minimum quantities unchanged](static/description/en/06_reguli_dupa_formula.png)
