## 19.0.1.0.3 (2026-10-22)

- Listed on Odoo Apps as *Competitors Price Tracker* (was *Competitors Price*). The technical name `deltatech_competitors_price` does not change.

## 19.0.1.0.2 (2026-10-02)

- Security: "Fetch" sent the HTTP request to any product URL, so a user could make the
  server call internal services (127.0.0.1, private networks, cloud metadata). Only
  http(s) URLs whose host resolves exclusively to public addresses are fetched now;
  redirects are followed manually (at most 5) and every hop is checked the same way.
  A rejected URL is reported in the fetch status. **Behavior change:** competitor URLs
  on an intranet/private address are no longer fetched.

## 19.0.1.0.1 (2026-09-29)

- Own module icon, instead of the generic gears it had.
