## 19.0.0.0.10

- Port from 18.0.0.0.15.
- Setup on install: create a per-company transit stock location and, on each
  warehouse, a two-step delivery operation type (with automatic second transfer)
  and a two-step reception operation type, wired to the warehouse main stock
  location and the transit location. Runs only at install, so databases already
  using the module are not affected.
- The second transfer can now be created manually only after the first transfer
  is validated, so the goods are actually in the transit location.
- The second transfer now inherits the quantity actually moved to transit, so
  the flow works even when the operator filled only the "Quantity" field and
  left the "Demand" at 0.
- Fixed the `is_transit_transfer` and `sub_location_existent` computes to work
  on multi-record sets (no more singleton errors) and removed the side effect
  from the compute method.
- Also carries the `sudo` fix for creating the second transfer (ticket 8970).
