Features:

- A security group can be attached to a Operation Type. Only users in this group can validate pickings of this type
- If left empty, no security group is required
- Adds another option, "Restrict done quantities to reserved", on the operation type: if checked, a picking cannot be
  validated when the done quantity of a move differs from its ordered quantity (demand), compared in the same unit of
  measure
- Adds another option, "Restrict new products", on the operation type: if checked, a picking cannot be validated when it
  has a done quantity on a product that was not ordered (a move added after confirmation or without ordered quantity)
