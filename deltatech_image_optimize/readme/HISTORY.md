# Changelog

## 19.0.1.8.1 (2026)

- ``data/ir_cron.xml`` is now ``noupdate="1"``. It was not, so **every module
  upgrade reapplied ``active = False`` and switched the scheduled action back
  off**, silently, however long ago someone had enabled it. Seen in production:
  the cron was enabled one day, an upgrade the next morning disabled it again,
  and nothing in the logs said so -- it simply never ran. ``ir_config_parameter.xml``
  already had the flag, which is why the tuned parameters survived the same
  upgrade while the cron did not.
- Existing databases: the flag stops future upgrades from touching the record,
  but it cannot restore a cron already switched off. Check
  Settings > Technical > Scheduled Actions after upgrading, and re-enable it if
  it was on before.

## 19.0.1.8.0 (2026)

- The batch methods now also return ``freed_disk``, and log it next to
  ``freed``. ``freed`` sums the per-attachment size difference, which
  **overstates the saving** whenever the same picture is used on several
  records: Odoo keeps one file per checksum, so recompressing one attachment
  frees nothing while the others still reference the old file. On a real
  deployment the run reported **29 GB** where the disk gave back about **4 GB**
  -- 815 000 image attachments living in 508 000 files. ``freed_disk`` counts
  only attachments whose file was not shared, so it is the figure to quote when
  someone asks how much space this recovers.
- The check reads ``store_fname`` (indexed, and derived from the checksum)
  before the write, since writing replaces it.
- ``readme/DESCRIPTION.md`` explains the difference, gives the SQL to measure
  real occupancy across the whole database, and notes that the filestore grows
  before it shrinks -- the space returns only once the GC runs.

## 19.0.1.7.0 (2026)

- **Transparent images now really become WebP.** They were silently falling back
  to optimized PNG on most databases. `odoo/tools/image.py` runs
  `Image.preinit()` and then sets `Image._initialized = 2`; preinit registers
  only BMP/GIF/JPEG/PPM/PNG, and the flag makes Pillow believe `init()` already
  ran, so `save(format="WEBP")` raises `KeyError: 'WEBP'` even where Pillow is
  built with libwebp and `features.check("webp")` returns True. The module now
  imports `PIL.WebPImagePlugin` explicitly, which registers the format —
  `Image.init()` alone does not help, it returns early on `_initialized >= 2`.
  Same approach already used by `deltatech_website_watermark`.
- `WEBP_OK` (a constant computed at import time) is replaced by
  `_webp_available()`, resolved on first use and cached. The old constant made
  the module behave **differently from one database to another**: where another
  module registering the WebP plugin happened to be imported first, transparent
  images became WebP; everywhere else the identical code produced PNG, with no
  error anywhere. Import order is not something a result should depend on.
- The test suite asks the module for WebP support instead of probing at import,
  so `test_transparent_image_becomes_webp` actually runs. It had been skipping
  itself with "Pillow build lacks WebP support" — on builds that encode WebP
  fine.

Impact: on catalogs with real transparency, those images now compress as WebP
(typically ~70% smaller than the PNG fallback) instead of staying nearly
uncompressed. No change for opaque images.

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
