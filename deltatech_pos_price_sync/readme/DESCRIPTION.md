This module pushes live product price changes to Point of Sale sessions that are already open.

Key features:
- Detects `list_price`/`standard_price` changes on products available in POS.
- Pushes a live bus notification to every open POS session, reusing the same channel pattern as `deltatech_pos_stock`.
- The POS frontend merges the fresh price straight into the in-memory model, without a page reload.
- Fixes the "changed the price, cashier still sees the old one even after F5" issue: a POS session that stays open never re-runs the write_date-based sync on reload.
