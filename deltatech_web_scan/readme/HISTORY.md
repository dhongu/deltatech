## 19.0.1.0.1 (2026-10-22)

- A normal page was reported as blocked by a protection against robots when it only loaded the
  detection script that Cloudflare adds to every page (`/cdn-cgi/challenge-platform/scripts/jsd/`,
  seen on granit-parts.ro), or when it had a CAPTCHA in a login or contact form. Only the challenge
  pages (Cloudflare "Just a moment...", DataDome, PerimeterX) and the answers 403, 429 and 503 count
  now. **Behavior change:** such pages are read instead of being marked *Blocked*.

## 19.0.1.0.0 (2026-10-22)

- First version: safe and polite reading of product pages (public addresses only, checked again when
  the connection opens, redirects checked, robots.txt, pause per site, protection against robots
  reported as blocked), schema.org extraction (JSON-LD, Microdata), selectors, price patterns,
  barcode and code checks, jump of price, the source and history mixins.
