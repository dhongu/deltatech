This module adds a physical location hierarchy (Storehouse > Zone > Shelf > Section > Rack), separate from standard Odoo stock locations, so you can track exactly where a lot/serial or product sits on the shelf.

1. Go to Inventory > Locations (menu added under the Locations root) and set up your hierarchy: Storehouse (linked to a warehouse location), then Zone, Shelf, Section and Rack records underneath it. Each Rack can have a barcode for scanning.
2. On a product's form, open the new **Locations** tab and set its default Storehouse/Zone/Shelf/Section/Rack. New lots/serials created for that product inherit these values automatically.
3. When a lot/serial moves into the product's master storehouse location, its rack/shelf/zone position is kept in sync automatically; when the quantity on hand for that lot drops to zero, its position is cleared.
4. To relocate a lot/serial with a barcode scanner, go to Inventory > Operations > Adjustments > Change lot: scan the lot/serial barcode, then scan the target rack's barcode, and press Apply (or Reset to start over).
5. The lot/serial and stock quant location fields (Storehouse/Zone/Shelf/Section/Rack) are also visible/reportable on `stock.lot` and `stock.quant` records.
