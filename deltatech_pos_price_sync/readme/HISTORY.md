## 20.0.1.0.2 (2026-10-28)

- Migrated to Odoo 20.0. The test closing an empty POS session uses `close_session_from_ui()`
  (`action_pos_session_closing_control()` no longer exists).

## 19.0.1.0.2 (2026-10-17)

- Saving a new price on a shared product together with a product of another company now still
  pushes the shared product to the open POS sessions of every company; before, only the sessions of
  the other company received the update (#3415).

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.

## 19.0.1.0.0 (2026-08-20)

- Initial version. `product.template` now pushes a live `PRICE_SYNCHRONISATION` bus notification
  (reusing the same `pos.bus.mixin` channel core uses for `notify_synchronisation`, same pattern as
  `deltatech_pos_stock`'s `STOCK_SYNCHRONISATION`) whenever `list_price` or `standard_price` changes
  on a product available in POS, to every open POS session. The frontend subscribes to it and merges
  the fresh `product.template` data straight into the in-memory model.
- Root cause: a POS session that stays open never
  re-runs the write_date-based sync on `loadInitialData()` (see `data_service.js`), so pressing F5
  kept showing the old price even though the change was saved on the backend.
