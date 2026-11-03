Standard putaway rules send a product to a fixed shelf, whether the shelf still has
room or not, and deliveries can reserve goods that were received but not yet put
away. This module gives shelves a capacity, keeps the putaway within it and adds
options on the operation type to control putaway and reservation.

**Shelf capacity**: on the location form (**Inventory > Configuration > Locations**),
section **Capacity**, the field **Max products (leaf)** sets the maximum quantity a
shelf can hold, counted in the product unit of measure, all products together. Zero
means no limit.

**Capacity and occupancy figures**: each location computes **Max products**,
**Current quantity** (on hand), **Planned quantity** (on move lines not yet done) and
**Occupancy** (current / max, between 0 and 1). For a parent location, the maximum and
the current quantity are the sum of its children. The fields are not shown in the
views of this module; they are meant for reports or for a warehouse map.

**Capacity-aware putaway**: a shelf that is full, or would be full with the quantity
already planned for it, is not proposed by the putaway. When a reserved line exceeds
the free room of its shelf, the line is split: the shelf gets what fits and the rest
goes to another shelf chosen by the putaway. At validation, a move whose destination
is a shelf with a capacity is blocked with an explicit error when it would overfill
the shelf. The standard storage category checks (weight, product and package
capacities, mixing of products) still apply.

**Search in sublocations**: with the system parameter
`deltatech_putaway_strategy.search_sublocation` set to `True`, when the location
given by the putaway rule has sublocations, the putaway first proposes a sublocation
that already holds the product, then the first shelf, in alphabetical order, that has
room.

**Prefer the shelf already holding the product**: with the system parameter
`deltatech_putaway_strategy.prefer_existing_stock_location` set to `True`, the putaway
looks for the shelves under the incoming location that already hold free stock of the
product, even outside the location given by the rule, and proposes the one with the
largest quantity that still has room. If the rule's shelf already holds the product,
or no such shelf has room, the putaway rule applies as usual. The source shelf of an
internal transfer is never proposed as its destination. Off by default.

System parameters are set in **Settings > Technical > System Parameters** (developer
mode).

**Operation type options** (**Inventory > Configuration > Operation Types**):

- **Avoid Putaway Rules**: the transfers of this operation type keep their destination
  location; no putaway rule is applied.
- **Avoid Root Location on Reservation** (deliveries only): the delivery never reserves
  stock placed directly in its source location, typically the warehouse stock root
  (e.g. `WH/Stock`). Goods that were received but not yet put away on a shelf are not
  allocated to sales orders; the shelves under it stay eligible. The option takes
  effect only when `deltatech_stock_removal_priority` is also installed.

## Limitations

- **Planned quantity** is computed only for shelves that have a capacity set; for
  parent locations it is always zero, not the sum of the children.
- On 20.0, quantities in another unit than the product unit (for example a dozen)
  are not converted: the planned quantity and the split compare the quantity of the
  line, in its own unit, with the capacity.
- On 20.0, a shelf filled exactly to its capacity keeps the reserved line: the line is
  not sent to another shelf, and the validation then refuses the transfer.
- On 20.0, the check at validation looks at the destination of the move only; when
  the move goes to the stock root and its lines to shelves, an overfilled shelf is
  not blocked.
