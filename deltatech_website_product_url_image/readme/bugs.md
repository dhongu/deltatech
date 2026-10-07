# Confirmed bugs — 2026-10-03

## URLIMAGE-001 — P2: removed Werkzeug parser breaks Python 3.12+ deployments

Both product image and template onchange/write call werkzeug.urls.url_parse outside their try/except. Local Odoo requirements select Werkzeug 3.0.1 for Python >=3.12; that version removes the deprecated URL helpers. Writes containing image_file_name or image name fail with AttributeError before downloading, including ordinary image renaming in product.image. Use urllib.parse.urlparse. Official history: https://werkzeug.palletsprojects.com/en/stable/changes/ (2.3 deprecation, 3.0 removal). Local Python3.11 library still has url_parse; failure not executed against an installed 3.0 library.

## URLIMAGE-002 — P1: unrestricted server-side URL fetching

- **Status:** Fixed in 19.0.1.0.4. The download is now the private `_load_image_from_url`, run only for
  users with write access on products (the onchange no longer fetches for read-only users). Only http/https
  URLs whose host resolves exclusively to public addresses are fetched (loopback, private, link-local,
  multicast and reserved IPv4/IPv6 ranges refused); redirects are followed manually (max 5) and each hop is
  revalidated; 15 s timeout, streamed body capped at 10 MiB, HTTP 200 and an `image/*` Content-Type required.

Public load_image_from_url passes caller URL directly to requests.get, without scheme/host/network restrictions; image validation happens after the request. An authorized RPC caller or product editor can direct the Odoo server to internal/loopback destinations, and redirects are not validated. Invalid image content does not undo a request already made. Restrict supported external sources, validate resolved targets and redirects, and enforce intended caller access. No internal/private network requests or exploit tests performed. Source-supported SSRF capability; exact deployment exposure/egress and endpoint effects unverified.

## Limits

All source and native image helper/view contracts read. No response size limit and 60-second timeout can consume resources; no measured resource attack asserted. HTTP failures are not checked before image decoding. No network image, database or browser tests executed.
