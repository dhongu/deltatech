## 19.0.1.0.4 (2026-10-07)

- Security: loading a product image from a URL no longer lets the server reach internal addresses (SSRF).
  Only public http/https hosts are fetched, every redirect is revalidated, the response is limited in time and
  size and must be an image, and only users allowed to edit products can trigger the download.

## 19.0.1.0.3 (2026-10-04)

- Add unit tests covering image loading from URL on product templates and product images (write and onchange).

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
