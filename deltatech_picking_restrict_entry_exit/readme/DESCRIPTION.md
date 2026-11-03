Receipts and deliveries should match what was ordered. This module stops warehouse users from
validating a receipt or a delivery that contains products not linked to a purchase or sales order,
or quantities larger than the demand.

**Receipts and deliveries tied to an order**: on **Validate**, every line with a quantity of a
receipt must come from a purchase order line, and every line of a delivery from a sales order line.
The check for receipts applies when Purchase (`purchase_stock`) is installed, the one for
deliveries when Sales (`sale_stock`) is installed.

**No quantity above the demand**: on **Validate**, a line whose done **Quantity** is larger than
the **Demand** blocks the validation. The same check runs when the transfer is saved after the
quantity of a line was changed.

**No lines added by hand**: a new line with a done quantity cannot be saved on a receipt or a
delivery; on other transfers such a line cannot have a done quantity larger than its demand.

**Exempt cases**: returns and backorders are not checked at validation, and neither are internal
transfers between two locations of the same warehouse.

## Configuration

Users in the **Picking create permission** group are exempt from the checks at validation and can
add lines on receipts and deliveries. At installation only the administrator is in the group; all
other users are restricted. To exempt another user, activate the developer mode, go to
**Settings > Users & Companies > Groups**, open **Picking create permission** and add the user.

## Limitations

- Creating a receipt or a delivery without a source order is not blocked; only its validation is.
- The check of the done quantity on save applies to every user, including the members of
  **Picking create permission**, and also to returns and backorders.
