# Confirmed bugs — 2026-10-03

## PURPHASE-001 — P2: automatic missing-phase creation exceeds ordinary user rights

set_phase searches by code then creates a missing phase in the caller's environment. ACL permits phase create only to purchase managers; ordinary internal/purchase users can only read. StockPicking.write maps delivery_state refused to phase refused, but the default data defines no refused phase. With deltatech_delivery_status installed and an otherwise authorized non-manager user updating a linked purchase receipt to refused, creation raises AccessError and the transaction cannot save the transfer. Deleting/renaming rfq or purchase_confirm similarly breaks ordinary RFQ sending/confirmation despite documented automatic fallback. Provide required phases and a narrowly scoped authorized fallback, or avoid making document updates depend on caller's configuration-creation rights.

Evidence: full Python/XML, auxiliary ACL CSV, default phase data and sibling delivery_state declaration read. Source-supported ACL failure; no database permission test executed. Actual stock/purchase record access must independently permit the attempted document operation.

## Integration limits

All eligible source and native view references checked. Delivery mapping requires the optional deltatech_delivery_status provider, absent from depends; without it native state updates do not write delivery_state, so the phase feature is dormant rather than an installation error. ignore_sequence is unused and last receipt event can move a shared order phase backwards; no monotonic/aggregate business policy asserted. Context skip_phase_update guard works on set_phase. No database upgrade/UI/permission tests executed.
