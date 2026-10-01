Upload the company watermark once, in the settings, and let other modules use it where it is
needed. This module stores the watermark image on each company and shows it in the General
Settings. It does not change any page or document by itself: the
[Website Watermark Image](https://apps.odoo.com/apps/modules/19.0/deltatech_website_watermark)
module uses it to mark the product pictures of the online shop.

- **One watermark per company**: Each company keeps its own watermark image. In a
  multi-company database, the setting applies to the current company.
- **Set in General Settings**: The image is uploaded in the Companies section of the settings,
  with a preview.
- **Base for Website Watermark**: Website Watermark Image applies it to the product pictures of
  the shop when they are displayed, so the original images stay clean.
- **Lightweight**: It depends only on the standard settings (`base_setup` and `web`), so other
  modules can build on it without pulling in the website.
