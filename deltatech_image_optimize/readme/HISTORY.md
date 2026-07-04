# Changelog

## 18.0.1.4.0 (2025)

- Transparency is now decided by the *actual* alpha content, not the mode:
  RGBA/palette images that are effectively opaque go to JPEG (big savings),
  only genuinely transparent images go to WebP. Palette images are normalized
  first. This fixes "transparent" PNGs that previously stayed uncompressed.
- Genuinely transparent images with no WebP support keep an optimized PNG
  (never flattened to a solid background).

## 18.0.1.3.0 (2025)

- Images with transparency are now converted to **WebP** (alpha preserved,
  ~70% smaller than PNG) instead of being kept as PNG. New `webp_quality`
  parameter (default 85).
- Because Odoo cannot resize WebP, a WebP original is written directly on its
  attachment (never through the record field, which would regenerate
  full-size variants); the variants are converted in place separately.
- Opaque images keep going to JPEG.

## 18.0.1.2.0 (2025)

- Configurable `flush_every` parameter (memory flush/invalidate/gc frequency).
  Lower it to 2-3 for very high-resolution images (e.g. 20 MP) so the cron and
  batch runs stay within memory on heavy images.
- `gc.collect()` at each flush point.
- The scheduled action now runs a filestore GC at the end (single writer →
  can grab the lock), so cron-driven runs actually reclaim disk space.

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
