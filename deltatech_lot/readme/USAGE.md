- Automatic lot/serial numbering on receipts: on an **incoming** (or
  dropship) transfer, if a product is tracked **By Lots** and no lot
  name was entered, validating the transfer (**Validate** button on the
  stock picking) automatically generates a lot number from the
  `stock.lot.serial` sequence.
- Lot location: each **Lot/Serial Number** (Inventory > Products >
  Lots/Serial Numbers) now shows a **Location** field, computed from its
  quants. It stays empty when the lot's stock is split across more than
  one location. The location is also shown as a column on the lot list
  and can be used as a filter in the Lots/Serial Numbers search view.
- When picking a lot on a delivery/operation line, the **Lot/Serial
  Number** field is automatically filtered to lots available in the
  transfer's source location.
