# Changelog

## 18.0.1.1.0 (2025)

- Step 2 — recompress the stored resized variants (image_1024/512/256/128)
  in place (`att.write({'raw': ...})`), at a configurable `variant_quality`,
  without resizing and without touching the original (no related write-back).
- New parameters: `variant_fields`, `variant_quality`, `variant_min_size`.
- The scheduled action now optimizes originals **and** variants.

## 18.0.1.0.1 (2025)

- Keep memory flat over large batches: flush and invalidate the ORM cache
  every 20 images (avoids the worker/shell being killed on big batches).
- Lower the default batch size to 200.

## 18.0.1.0.0 (2025)

- Initial release.
- Add ``ir.attachment.deltatech_image_optimized`` marker field.
- Recompress original image attachments (``image_1920`` / ``image_variant_1920``):
  downscale to ``max_dim``, JPEG (quality tuned) for opaque images, optimized
  PNG for images with alpha, skip animated GIFs.
- Write the optimized image back through the owning record so Odoo regenerates
  the resized variants from the smaller original.
- Configurable via ``ir.config_parameter`` (quality, max_dim, min_size, batch,
  target_fields).
- Daily scheduled action ``Image Optimizer: recompress oversized images``,
  disabled by default.
