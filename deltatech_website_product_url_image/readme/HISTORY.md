## 19.0.1.0.6 (2026-10-22)

- Listed on Odoo Apps as *Product Image from URL* (was *eCommerce Product Image URL Link*). The technical name `deltatech_website_product_url_image` does not change.

## 19.0.1.0.5 (2026-10-17)

- Fix: saving or renaming a product image, or setting the image file name on a product, no longer fails with
  `AttributeError` on servers with Werkzeug 3 (Python 3.12+); URLs are now detected with the standard library.

## 19.0.1.0.4 (2026-10-07)

- Security: loading a product image from a URL no longer lets the server reach internal addresses (SSRF).
  Only public http/https hosts are fetched, every redirect is revalidated, the response is limited in time and
  size and must be an image, and only users allowed to edit products can trigger the download.

## 19.0.1.0.3 (2026-10-04)

- Add unit tests covering image loading from URL on product templates and product images (write and onchange).

## 19.0.1.0.2 (2026-09-29)

- Own module icon, instead of the generic gears it had.
