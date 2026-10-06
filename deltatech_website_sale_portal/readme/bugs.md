# Confirmed bugs — 2026-10-03

## SALEPORTAL-001 — P2: pagination loses active search

The addon filters native quotation/order domains using request.params search/search_in, but does not add these parameters to the native pager. Native _prepare_sale_portal_rendering_values builds url_args only from date_begin/date_end/sortby. Search producing multiple result pages has filtered count/results on page1, but clicking page2 sends no search parameters: the next request uses the full accessible order domain and pagination no longer represents the search. Carry search and search_in into pager URL arguments.

Evidence: full controller/template source and native sale portal rendering/pager construction read. Source-supported request flow; no multi-page portal/browser test executed.

## SALEPORTAL-002 — P2: submitted search text disappears from input

Route overrides set searchbar_inputs and search_in in response.qcontext, but do not set search. Native sale rendering values do not include search; portal.searchbar renders the input with t-att-value=search. A search applies to the current result set but its input is blank after rendering, losing the visible active criterion. Add search to rendering values consistently with domain and pager handling.

Evidence: native portal search input value and addon/native qcontext dictionaries read. Source-only, no browser rendering test executed.

## Limits

Full eligible source and native table/loop anchors checked. Domain.AND preserves native partner ownership/domain and model ACLs before native sudo on selected display records; no cross-customer leak established. Invalid search_in yields no extra search predicate; policy validation rather than a security claim. No database/access/browser tests executed.
