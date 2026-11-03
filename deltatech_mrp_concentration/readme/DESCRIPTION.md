Recomputes the quantity of the main ingredient of a recipe from the concentration you want in the
finished product and the concentration of the ingredient you have, then balances the batch with a
diluent or a by-product. Meant for chemical, food or pharmaceutical products made by diluting or
concentrating an active ingredient.

**Concentrations on the bill of materials.** The BoM form gets two fields next to the product:
*Concentration* (of the finished product) and *Concentration Primary* (of the main ingredient). Both
are plain numbers, so use the same unit for both, for example percentages.

**Ingredient type on the components.** Each component line gets an *Ingredient Type*: *Primary* (the
active ingredient), *Secondary* (the diluent) or *Normal* (default, not recalculated).

**Recalculation on the BoM.** When you change either concentration or the BoM quantity, the
*Primary* component quantity becomes BoM quantity × *Concentration* / *Concentration Primary*. The
rest of the batch is balanced:

- dilution (the result is below the BoM quantity): the *Secondary* component gets the difference;
- concentration (the result is above the BoM quantity): the by-products get the excess and the
  *Secondary* component is set to zero.

**Recalculation on the manufacturing order.** The MO form shows the same two fields, copied from the
BoM when you pick it. Changing a concentration or the quantity to produce recalculates the demand of
the primary and secondary components and of the by-products of that order with the same rule, so the
actual concentration of a received lot can be used for one order without changing the BoM.

**Where to find it.** *Manufacturing > Products > Bills of Materials* for the BoM, and
*Manufacturing > Operations > Manufacturing Orders* for the orders. The by-products are entered on
the *By-products* tab of the BoM, available when *By-Products* is enabled in the Manufacturing
settings.

## Limitations

- The recalculation runs only while editing the BoM or the MO form. Orders created automatically
  (from a sales order or a replenishment rule) do not get the concentrations and keep the BoM
  quantities until the fields are changed on the form.
- When the BoM has several by-products, they all receive the same excess quantity.
