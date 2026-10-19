Never ship half a kit: when a product sold as a kit (a Bill of Materials of type
**Kit**) is marked as restricted, the delivery cannot be validated unless its
components are present in the same transfer in the proportions of the Bill of
Materials.

- **Enabled per Bill of Materials**: the **Restrict Incomplete Delivery** option
  appears on Bills of Materials of type Kit; kits without it are delivered as in
  standard Odoo.
- **Every component in the transfer**: if a component of the kit is missing
  from the transfer, validation stops with a message naming the product, the
  transfer and the kit.
- **Quantities in proportion**: the done quantity of each component must match
  the Bill of Materials ratio against the first component, compared with the
  rounding of the unit of measure; a mismatch stops validation and names the
  component.
- **Partial deliveries allowed**: a transfer may deliver fewer sets than
  ordered (for example 1 of 2), as long as the components stay in proportion.
- **Sales deliveries only**: the check applies to transfer lines generated from
  a sales order line; other transfers are not affected.
- **Clear blocking message**: when several transfers are validated together,
  the errors of all of them are shown in one message and none is validated.
