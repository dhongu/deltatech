# Confirmed bugs — 2026-10-03

## POSPRICE-001 — P2: mixed shared/company-specific batch skips some sessions

`models/product_template.py:25–27` collects nonempty company IDs across the entire changed template batch and restricts all destination sessions to those companies. Changing prices together on a shared template and a company-B template sends only to B, so company-A POS sessions keep the shared product's previous price. Select applicable products per configuration, including shared products for every relevant company. This repeats POSSTOCK-001 in the separate price notification path.

Evidence: exact `_notify_pos_price_change()` executed with a mixed shared/B batch and captured session-domain/recipients; only B receives the event. Native bus/read/hydration contracts and sibling stock patch compared. Isolated ORM doubles only; no database/bus/browser integration executed.

## Review limits

Full eligible module source read. Native websocket API and cooperative processServerData super chain match the stock-sync sibling patch. Company-dependent full product payloads and in-flight event ordering remain database/browser integration limits. No measured test-line coverage.
