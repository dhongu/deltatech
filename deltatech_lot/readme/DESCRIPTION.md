Generates lot numbers on supplier receipts and shows where each lot is stored.

- **Lots generated on validation**: When a receipt from a vendor (or a dropship) is validated, every
  line of a product tracked by lots that has no lot number gets the next number of the **Serial
  Numbers** sequence, one lot per line. Lots typed by the user are kept.
- **Lot location**: The **Location** field of the lot shows the location that holds all its stock
  (empty when the lot is spread over several locations), on the lot form for every inventory user and
  as a column in the list of lots.
- **Search by location**: The list of lots can be searched by **Location**.
