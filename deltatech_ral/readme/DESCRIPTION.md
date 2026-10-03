Features:

- Allows the selection of a pigment (RAL) in production order.
- The pigment is a material which have code that starts with RAL.
- If in BOM it is used the pigment RAL 0000 it will be replaced with the pigment from production order.
- The batch will be created automatically upon order confirmation and will have the pigment from production order.

Instruction:

- Create the product "Dummy RAL" and set it's internal reference to "RAL 0000".
- In the BOM a the product that uses pigments set the "Dummy RAL" as a component (WITHOUT SELECTING A VARIANT).
- In the final product should have a colour type attribute
- Create the pigment products with internal reference "RAL color" where you substitute 'color' with the name of the of
  the option from the attribute of the final product (e.g. RAL White, RAL Rose etc.)
- When creating the production order for a variant the dummy RAL product will be replaced with the corresponding RAL
  pigment.
