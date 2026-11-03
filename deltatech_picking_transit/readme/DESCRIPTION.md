Moves goods between two warehouses in two steps, through a transit location:
the sending warehouse ships the goods to transit, and the receiving warehouse
gets its own transfer, with the same products, from transit to its stock.

**Operation types for the two steps.** On an internal operation type you set
**Two Step Transfer Use**: *Delivery* for the transfer that sends the goods to
the transit location, *Reception* for the transfer that brings them from transit
into the receiving warehouse.

**Create Transfer button.** On an internal transfer whose operation type is
marked *Delivery* and that has no **Source Document**, the **Create Transfer**
button opens a wizard where you choose the reception **Operation Type**. The
module creates and confirms the second transfer, from the destination of the
first transfer to the default destination of the chosen operation type, with
the same products and quantities. Each transfer gets the address of the other
warehouse as contact, and both are linked by chatter messages. The button
disappears once the second transfer exists.

**Automatic second transfer.** When **Auto Second Transfer** is checked on the
*Delivery* operation type, the second transfer is created when the first one is
validated, without the wizard. The receiving warehouse is the one whose
**Address** is the **Contact** of the transfer, and its internal operation type
marked *Reception* is used. Transfers with a **Source Document** (replenishment,
sale orders) are skipped, since their receiving transfer already exists.

**Checks on reception.** The second transfer can be validated only with products
that come from the first transfer or its backorders. A backorder of the first
transfer does not create another second transfer: a chatter message tells which
transfer will receive its products.

**Reassign Location (optional).** When the system parameter
`deltatech_picking_transit.use_sub_locations` is set, internal transfers show a
**Reassign Location** button that sets, on each detailed operation, the first
sublocation of the source location that has the product in stock.

## Configuration

1. Create a transit location and, in *Inventory > Configuration > Warehouse
   Management > Operations Types*, an internal operation type in the sending
   warehouse with the transit location as default destination. Set **Two Step
   Transfer Use** to *Delivery* and, if you want, check **Auto Second Transfer**.
2. In the receiving warehouse, create an internal operation type with the
   transit location as default source and set **Two Step Transfer Use** to
   *Reception*.
3. For the automatic mode, fill in the **Address** of each warehouse and use it
   as **Contact** on the delivery transfer.

## Limitations

- The first transfer stays editable after the second transfer is created;
  changes are not copied to the second transfer.
- On 20.0, opening or reloading a *Delivery* transfer whose second transfer is
  not created yet switches its lock (locked / unlocked) each time; check the
  lock state before editing it.
