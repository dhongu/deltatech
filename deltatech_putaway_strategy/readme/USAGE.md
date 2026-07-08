1. Set **Max products (leaf)** on leaf locations that should have a
   maximum capacity.
2. Use standard operations (receipts, internal transfers). The putaway
   helper will:
   - reject over-capacity destinations,
   - split move lines automatically when needed,
   - and try to choose a location with existing stock first when
     appropriate.
3. The computed capacity fields can be displayed in location views or
   used by other modules (e.g., visual warehouse map).

Configuration:

- To enable sub-location search (prefer locations with existing stock),
  go to **Settings > Technical > System Parameters** and set
  `deltatech_putaway_strategy.search_sublocation` to `True`.
- To disable putaway rules for a specific operation type, open
  **Inventory > Configuration > Operations Types** and enable **Avoid
  Putaway Rules**.
- To exclude the root source location from reservation, enable **Avoid
  Root Location on Reservation** on the operation type.
