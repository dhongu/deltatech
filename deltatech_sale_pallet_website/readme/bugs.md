# Confirmed bugs — 2026-10-03

## WEBPALLET-001 — P2: verification runs before pallet changes

_verify_cart_after_update calls super first, then creates/updates/deletes pallet lines. Native website_sale verification recalculates carrier.rate_shipment and saves website_sale_cart_quantity from the current cart. New or changed pallet lines therefore are absent from that calculation, leaving delivery price and session quantity inconsistent until a later verification. Generate/reconcile pallet lines before the final native verification. The sibling extra-line addon correctly does its reconciliation before super; installing it does not repair pallets added after the super chain returns.

Evidence: complete addon and native website_sale verification (:674–690), sibling extra/cart hook source read. Carrier impact depends on rate algorithm; session quantity stale whenever relevant counted quantity changes. No live request/carrier test executed.

## WEBPALLET-002 — P2: removing last source product leaves pallet in cart

Same missing-key reconciliation as base PALLET-003. Pallet dictionary only includes products still requiring a pallet. If the last main product is removed, no key exists for its generated pallet, so neither quantity update nor unlink runs; the pallet line remains chargeable. Explicitly reconcile generated ownership against current demand.

Evidence: full website loop and base recompute_pallet_lines read. Existing key with computed zero does unlink correctly; this finding concerns absent source keys. No cart/database test executed.

## Limits

Native cart add/update calls this verification hook. Product-details QWeb anchor and base product fields exist. Template shows template list-price currency rather than active website pricelist: pricing policy/configuration validation needed before asserting a separate display defect. No browser/QWeb/carrier/database tests executed.
