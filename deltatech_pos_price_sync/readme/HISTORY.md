## 19.0.1.0.0 (2026-08-20)

- Initial version. `product.template` now pushes a live `PRICE_SYNCHRONISATION` bus notification
  (reusing the same `pos.bus.mixin` channel core uses for `notify_synchronisation`, same pattern as
  `deltatech_pos_stock`'s `STOCK_SYNCHRONISATION`) whenever `list_price` or `standard_price` changes
  on a product available in POS, to every open POS session. The frontend subscribes to it and merges
  the fresh `product.template` data straight into the in-memory model.
- Root cause (Terrabit ticket #9305, client Damira COM SRL): a POS session that stays open never
  re-runs the write_date-based sync on `loadInitialData()` (see `data_service.js`), so pressing F5
  kept showing the old price even though the change was saved on the backend.
