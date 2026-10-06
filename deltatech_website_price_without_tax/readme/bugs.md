# Confirmed bugs — 2026-10-03

## WEBNETPRICE-001 — P2: reprocessing display price does not yield net price

_get_combination_info receives list_price already converted by native _apply_taxes_to_price into website display semantics, then calls mapped taxes.compute_all(list_price) with default handle_price_include. If website displays tax included but the tax is configured price excluded, a base100 with21% tax arrives as121; compute_all treats121 as an excluded base and total_excluded remains121, falsely labelled net. Conversely, with a price-included tax and tax-excluded website, native net100 is reinterpreted as gross and reduced to about82.64. Compute net from the original normalized base, or reverse the displayed gross using explicit display semantics, not tax price_include alone.

Evidence: all module source and native website_sale combination tax preparation/_apply_taxes_to_price (:649–675,696–714) plus compute_all contract read. Arithmetic/source proof; no database fiscal-position/browser scenario executed.

## Integration limits

Mapped taxes are correctly exposed by native combination info and consumed here; obsolete missing-taxes assumption excluded. The method uses list_price before discount rather than actual price; discounted net-display intent needs validation before separate finding. Currency and partner are not passed to compute_all, so rounding/context may differ; no measured concrete mismatch asserted. Full migration source read: temporary generic-view deactivation/reactivation is parameterized SQL; actual legacy/COW architectures and database upgrade not executed. QWeb anchor exists; dynamic variant-price refresh requires browser testing. No DB/tax/browser/upgrade tests or fixes.
