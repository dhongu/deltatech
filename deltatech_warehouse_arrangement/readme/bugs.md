# Known bugs

Review date: 2026-10-02. Target version: Odoo 19.

## ARRANGE-001 — P2: Scanning another lot retains the previous rack selection

- **Status:** Open.
- **Location:** wizard/lot_set_location.py, on_barcode_scanned()/do_change().
- **Trigger:** Scan lot A and rack R, then scan lot B without pressing Reset; press Apply before scanning a rack for B.
- **Actual behavior:** The successful lot branch sets lot_id and lot_scanned but leaves rack_id untouched. do_change only checks both fields are set, then writes the old rack's full hierarchy to the newly selected lot.
- **Evidence:** Executed the actual scan method extracted by AST with lot A and rack 70 already selected. Scanning lot B changed lot_id to 2 while rack_id remained 70. Apply source inspected; no database lot modified.
- **Impact:** The operator can silently assign a lot to a stale rack, misdirecting subsequent picking/location lookups.
- **Suggested fix:** Clear rack selection whenever the lot changes and require a fresh rack confirmation before applying; also define safe behavior for ambiguous lot scans.
- **Validation needed:** Consecutive lots with/without Reset, new lot before new rack, ambiguous names and invalid scans; Apply must not reuse another lot's rack accidentally.

## ARRANGE-002 — P2: Lot creation overwrites explicitly supplied storage locations

- **Status:** Open.
- **Location:** models/stock_lot.py, create().
- **Trigger:** Create a lot with explicit loc_storehouse_id/zone/shelf/section/rack values different from the product template defaults, including a product without defaults.
- **Actual behavior:** The override unconditionally assigns all five keys from product_id into each vals dictionary. Explicit caller values are replaced; if product defaults are unset, supplied locations become false.
- **Evidence:** Full create override inspected. Each assignment uses vals[key] = product.field.id with no setdefault or presence check. Product and lot forms expose independent location fields, and the location-change wizard supports per-lot assignments. No Odoo create executed.
- **Impact:** Imports and explicit lot creation cannot preserve the lot's actual rack/location, instead recording the product default or no location.
- **Suggested fix:** Use product locations only as defaults for omitted keys, validate hierarchy consistency and preserve explicitly supplied lot locations.
- **Validation needed:** Explicit locations with differing/unset product defaults, omitted locations, multi-create batches and context product defaults.

## Review limitations

All eligible Python/XML source manually reviewed, including hierarchy/display computations, quant related fields, stock movement/depletion handling, barcode wizard, ACLs, forms and rack report. Only the isolated scan-method reproduction was executed; no database movement, lot create/update, label rendering or integration test run.
