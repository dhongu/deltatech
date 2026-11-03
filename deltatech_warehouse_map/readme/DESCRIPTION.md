In a warehouse organized as a deep location tree (zones, lines, racks,
shelves, cells), the standard Locations list does not show where space is
left. This module adds a visual map of the location hierarchy, colored by
occupancy, so you can see at a glance which racks and cells are full and
drill down to the products stored in a cell.

**Location map.** For a selected location, the map shows each child location
as a bar and nests all its descendants underneath, level by level. Click a
location name to open the map one level lower; the back button in the
header returns to the parent location.

**Occupancy colors.** Each bar is filled in proportion to the occupancy of
that location and shows the percentage and the current quantity. The fill is
green below 60%, yellow from 60% to 90% and red from 90%. A tooltip shows the
full location name, the occupancy and the current / maximum quantity. The
percentage and the quantity on each bar open *Current Stock*: the stock of
that location and of its sublocations, grouped by product.

**Cell contents.** When the selected location has no children, the map lists
the products stored in it with their on-hand quantity.

**Opening the map.** The **Map** button on each line of *Inventory >
Configuration > Locations* and the **Open Map** smart button on the location
form open the map for that location. The map of the main *Stock* location is
also available at the URL `/deltatech/warehouse_map`.

## Configuration

Capacity and occupancy come from the `deltatech_putaway_strategy` module,
installed as a dependency: set **Max products (leaf)** on the leaf locations
(the cells); the maximum, the current quantity and the occupancy of the
parent locations are summed from their children. Occupancy is the on-hand
quantity of the location divided by its maximum.

The map is available only to users of the *Inventory / User* group; access
rights and multi-company rules apply to the locations and quantities shown.

## Limitations

- There is no menu entry for the map; open it from a location or by URL.
- The labels of the map page are in Romanian and are not translated.
