**Automatic substitution**

1. Create a manufacturing order for a product whose BoM has components set to
   *Automatic*.
2. Click **Confirm**. For each such component, the stock of the original product in the
   source location is used first; the missing quantity is taken from the alternatives in
   stock, in their order, and added as new component lines.
3. If the stock arrives later, **Check Availability** repeats the substitution for the
   quantity still missing.

**Manual substitution**

1. On a confirmed manufacturing order, the components with alternatives show an
   **exchange** button.
2. The dialog shows the free and forecasted stock of the original component and of each
   valid alternative. Choose the alternative and the quantity of the original component to
   replace; the quantity of the alternative is converted automatically.
3. Click **Substitute**. The original line keeps the rest of its quantity, a new line is
   added for the alternative, and a message is logged on the order.

**Report**

- **Manufacturing > Reporting > Component Substitutions** lists the substituted moves,
  with the replaced component, the component consumed instead, the quantity and whether the
  substitution was manual or automatic.
