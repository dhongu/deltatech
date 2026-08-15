# Changelog

## 19.0.1.6.0 (2026)

- Document that `force_jpeg` is **destructive**, in both places where it is read:
  `readme/DESCRIPTION.md` and the comment above the parameter in
  `data/ir_config_parameter.xml`. It flattens transparency to black and the
  original cannot be recovered, because the optimized image is written through
  the record and the previous attachment is gone.
- Add a probe snippet that measures how much of a catalog has real transparency
  *before* the parameter is enabled, using `_dt_image_recompress` (a pure
  function — it returns bytes and format, writes nothing).
- The rationale is a real deployment: `force_jpeg=1` was enabled on a catalog
  believed to have no transparency, and 32% of a 40-image sample turned out to
  have real alpha. The first 20 optimized images were destroyed before it was
  caught.
- Bring the configuration table in `DESCRIPTION.md` up to date: it was missing
  `flush_every`, `force_jpeg`, `webp_quality` and the three `variant_*` keys, and
  still advertised the old `batch` default of 1000. Also state that transparent
  images go to WebP, with PNG as the fallback when the Pillow build has no WebP
  encoder.

## 19.0.1.5.1 (2026)

- Migration to Odoo 19.0. No functional change: the module only relies on
  stable `ir.attachment` API (`raw`, `res_field`, `_gc_file_store`) which is
  unchanged in 19.0.
- Add the Odoo Apps marketing banner (`static/description/main_screenshot.png`).

## 18.0.1.5.1 (2025)

- Lower the default/installed `batch` from 200-1000 to **50**. On production,
  a large batch of big/high-resolution images could exceed the cron worker's
  time/CPU limit; the resulting interrupt looked like a normal per-image
  failure and left the rest of that batch silently flagged as "processed"
  without actually being optimized. A small batch keeps each cron run well
  within limits. If you raise it, verify converted images actually shrank.

## 18.0.1.5.0 (2025)

- New `force_jpeg` parameter: when the catalog images are never really
  transparent (solid colored background), set it to 1 to ignore the alpha
  channel and always produce JPEG (max savings, no WebP dependency).

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
