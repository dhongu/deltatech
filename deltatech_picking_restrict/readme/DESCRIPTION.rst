Features:
 - A security group can be attached to a Operation Type. Only users in this group can validate pickings of this type
 - If left empty, no security group is required
 - Adds another option, "Restrict done quantities to reserved", on move type, if the option is checked you can't validate a picking if the done quantity is different than the reserved quantity
 - Adds another option, "Restrict new products", on move type, if the option is checked you can't validate a picking if there are product where the reserved quantity is 0 but the done quantity is different that 0
