In a warehouse where each team handles its own product families, the transfers ready to be
processed should go to the people of the right team, and the work should be spread evenly among
them. This module links product categories to a user group and assigns the responsible of the
transfers from that group.

**User Group on the product category**: adds the **User Group** field on the product category form.
The members of this group are the people who handle the products of the category.

**Responsible button on the transfer list**: select transfers in a transfers list and click
**Responsible** to fill in their **Responsible**. Only transfers in state **Ready** without a
responsible are processed; the others are left as they are.

**Balanced assignment**: for each transfer, the module collects the user groups of the categories
of its products, up to three parent levels, and takes their members that are active internal users
with the Inventory **User** right and allowed in the company of the transfer. Among them, a user
without any Ready transfer is chosen first; otherwise the one with the fewest Ready transfers in that
company.

The button is visible to Inventory **Administrator** users. The `responsible_determination` method
can also be called from custom code, for example after the reservation.

## Limitations

- The assignment is not automatic: it runs only from the **Responsible** button or from code that
  calls it.
- Only the direct members of the group are taken into account, not the users who get it through an
  implied group.
