# Confirmed bugs — 2026-10-03

## DIMENSION-001 — P2: zero dimension leaves previous volume

_onchange_dimension assigns volume only when all three dimensions are truthy. Enter 100 cm on each dimension (volume 1), then set one dimension to zero: previous volume 1 is retained even though the dimension product is zero. Logistics using volume therefore retain an incompatible value. Assign zero or explicitly reset volume when dimensions are incomplete according to policy.

Evidence: full method and native writable/inverse volume contract read. Source/arithmetic proof, no form/database test executed.

## DIMENSION-002 — P2: cubic-feet configuration receives cubic-meter number

View labels dimensions cm; method divides their product by 1,000,000 and directly writes volume, always a cubic-meter value. Native product._get_volume_uom_id_from_ir_config_parameter (:380–391) interprets volume in cubic feet when product.volume_in_cubic_feet=1. A 100×100×100 cm product becomes 1 cubic foot instead of approximately 35.315 cubic feet. Convert from cubic meters into the configured native volume unit.

Evidence: complete source, native unit configuration helper and view label read; source/arithmetic proof only, no configured database/UI test.

## Limits

Native volume view anchors exist. Onchange-only behavior does not update imports/RPC writes; dimension fields are documented as additional inputs and automatic persistence policy outside forms is not asserted as a third defect. Multi-variant template volume inverse follows native behavior; not database-tested. No source fixes applied.
