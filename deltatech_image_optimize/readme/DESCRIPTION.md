# Image Optimizer

Recompresses oversized **original** image attachments (``image_1920`` and
``image_variant_1920`` by default) to reclaim filestore space.

For each targeted image the module:

- downscales it to a maximum side of ``max_dim`` pixels (default 1920);
- re-encodes photos without transparency as progressive **JPEG** at the
  configured quality (default 85);
- keeps images with transparency as optimized **PNG** (alpha preserved);
- skips animated GIFs (never flattens the animation);
- keeps the result only when it is actually smaller.

The optimized image is written back **through the owning record**, so Odoo
regenerates the resized variants (``image_1024/512/256/128``) from the new,
smaller original.

Processed attachments are flagged (``deltatech_image_optimized``) and skipped on
the next run. Because Odoo creates a fresh attachment whenever an image field is
updated, newly uploaded or changed images are picked up automatically.

## Configuration

System Parameters (Settings → Technical → System Parameters):

| Key | Default | Meaning |
| --- | --- | --- |
| ``deltatech_image_optimize.quality`` | 85 | JPEG quality (1..95) |
| ``deltatech_image_optimize.max_dim`` | 1920 | max side in pixels |
| ``deltatech_image_optimize.min_size`` | 102400 | only images larger than this (bytes) |
| ``deltatech_image_optimize.batch`` | 1000 | images per cron run |
| ``deltatech_image_optimize.target_fields`` | image_1920,image_variant_1920 | fields to optimize |

## Scheduled action

``Image Optimizer: recompress oversized images`` runs daily. It is
**disabled by default** — review the configuration, test on staging, then
enable it.

For a large one-time backlog you can loop the batch method from the shell:

```python
while env["ir.attachment"]._dt_image_optimize_run(limit=200)["scanned"]:
    env.cr.commit()
```
