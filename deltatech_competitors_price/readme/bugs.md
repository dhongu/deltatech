# Bug review — Competitors Price

Review date: 2026-10-02. Target version: Odoo 19.

## COMPETITOR-001 — P1: Internal users can direct server HTTP requests to arbitrary addresses

- **Status:** Fixed in 19.0.1.0.2 — `_do_fetch()` goes through `_get_public_url()`: `_check_public_url()` accepts only http(s) URLs whose host (literal IP or every DNS answer) is a global, non-multicast address, IPv4-mapped IPv6 included; redirects are disabled in `requests.get` and followed manually (max 5), each hop validated. The internal-user ACL is unchanged. Covered by tests in `tests/test_ssrf.py` (loopback/private/link-local/IPv6/mapped/mixed DNS, non-http schemes, redirect to a private host, public redirect, redirect loop).
- **Location:** models/competitor_price.py, _do_fetch() and action_fetch_price(); security/ir.model.access.csv.
- **Trigger:** An internal user creates/edits a competitor record with a loopback/private service URL and invokes Fetch.
- **Actual behavior:** Full internal-user CRUD allows arbitrary product_url. The public fetch action calls requests.get directly with that URL, without validating host/address class or restricting destinations to approved competitor sites. Standard redirects are not constrained either.
- **Evidence:** Actual AST-extracted _do_fetch with product_url=http://127.0.0.1:8069/ passed that exact URL to a mocked HTTP client and completed successfully. ACL gives base.group_user full rights; no additional group or URL validation exists in the module. No real HTTP request was sent.
- **Impact:** A user can make the Odoo server reach local/private services unavailable to that user's browser. Response status/errors or extracted prices can expose limited service information; successful exploitation depends on reachable services and deployment network controls.
- **Suggested fix:** Restrict fetch permission and validate approved HTTP(S) competitor destinations, including resolved addresses and every redirect. Reject loopback/private/link-local addresses unless a separately authorized use case explicitly requires them.
- **Validation needed:** Public competitor site, loopback/private/link-local destinations, redirects to private hosts, DNS resolution changes and ordinary unauthorized internal users, using controlled fake endpoints.

## Review limitations

All eligible Python/XML and access CSV were read. HTTP interaction was mocked; no external/private network access or Odoo database tests executed. Microdata parser edge cases remain candidates requiring confirmation against actual extractor output and were not entered as confirmed findings.
