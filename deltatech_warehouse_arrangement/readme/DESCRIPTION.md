Keeps the physical arrangement of the warehouse in parallel with the standard Odoo stock locations, on
five levels: storehouse, zone, shelf, section and rack. The goods are found on the right rack without
creating an Odoo stock location for each of them.

Features:

- Storehouse → Zone → Shelf → Section → Rack hierarchy (menu *Inventory > Locations*), each level
  showing its full path; a storehouse is linked to its main Odoo stock location.
- Rack barcode and printable rack labels (Code128 barcode and full path).
- Default arrangement on the product; every lot / serial number keeps its own arrangement.
- A new lot takes the arrangement of its product; a lot received into the main location of the
  storehouse takes it again, and its arrangement is cleared when the lot runs out in that location.
- Arrangement columns, search fields and group-by options in the stock list
  (*Inventory > Reporting > Locations*).
- Barcode screen to scan a lot and its new rack (*Inventory > Operations > Adjustments > Change lot*).
- Only the *Warehouse Locations manager* group can create or change the hierarchy.
