1. Create a product named "Dummy RAL" and set its internal reference to
   `RAL 0000`.
2. In the Bill of Materials of the product that uses pigments, add "Dummy
   RAL" as a component (without selecting a variant).
3. Make sure the final product has a colour-type attribute.
4. Create the actual pigment products with internal reference `RAL <color>`,
   substituting `<color>` with the name of the colour attribute value on the
   final product (e.g. `RAL White`, `RAL Rose`, etc.).
5. When a Manufacturing Order is created for a variant of the final product,
   the **RAL** field on the order is set automatically from the product's
   colour attribute, and the "Dummy RAL" component is replaced with the
   matching RAL pigment on the raw material moves.
6. When the finished lot/serial number is generated, it is also stamped with
   the RAL pigment used, and the RAL is shown on the lot form/list.
