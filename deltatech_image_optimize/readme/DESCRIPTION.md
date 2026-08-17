# Image Optimizer

Recompresses oversized **original** image attachments (``image_1920`` and
``image_variant_1920`` by default) to reclaim filestore space.

For each targeted image the module:

- downscales it to a maximum side of ``max_dim`` pixels (default 1920);
- re-encodes photos without transparency as progressive **JPEG** at the
  configured quality (default 85);
- keeps genuinely transparent images as **WebP** (alpha preserved), or as
  optimized **PNG** when the Pillow build has no WebP encoder;
- skips animated GIFs (never flattens the animation);
- keeps the result only when it is actually smaller.

The optimized image is written back **through the owning record**, so Odoo
regenerates the resized variants (``image_1024/512/256/128``) from the new,
smaller original.

Processed attachments are flagged (``deltatech_image_optimized``) and skipped on
the next run. Because Odoo creates a fresh attachment whenever an image field is
updated, newly uploaded or changed images are picked up automatically.

## How much space you actually get back

The batch methods return two figures, and the difference between them matters:

| Key | Meaning |
| --- | --- |
| ``freed`` | sum of the per-attachment size difference |
| ``freed_disk`` | only the attachments whose filestore file was **not** shared |

Odoo stores one file per checksum, so attachments with identical content share
a single file. Recompressing one of them frees nothing while the others still
point at the old file. On a catalog that reuses the same picture across
products, ``freed`` therefore overstates the saving — on a real deployment it
counted **29 GB** where the disk gave back about **4 GB**, because 815 000 image
attachments lived in 508 000 files.

Use ``freed_disk`` when you report space. Use ``freed`` only to see how much
lighter the images themselves got — which is the real win on a website, since
that is bytes off every page load, regardless of deduplication.

To measure the whole database rather than one run:

```sql
SELECT pg_size_pretty(sum(sz)) FROM (
    SELECT DISTINCT ON (checksum) file_size AS sz
    FROM ir_attachment WHERE res_field IS NOT NULL AND checksum IS NOT NULL
    ORDER BY checksum, id
) t;
```

Note also that the filestore grows *before* it shrinks: the new file is written
while the old one is still referenced, and the space comes back only when the
filestore GC runs (the scheduled action does it at the end of each pass).

## Configuration

System Parameters (Settings → Technical → System Parameters):

| Key | Default | Meaning |
| --- | --- | --- |
| ``deltatech_image_optimize.quality`` | 85 | JPEG quality (1..95) |
| ``deltatech_image_optimize.max_dim`` | 1920 | max side in pixels |
| ``deltatech_image_optimize.min_size`` | 102400 | only images larger than this (bytes) |
| ``deltatech_image_optimize.batch`` | 50 | images per cron run |
| ``deltatech_image_optimize.flush_every`` | 20 | flush/invalidate the ORM cache every N images |
| ``deltatech_image_optimize.target_fields`` | image_1920,image_variant_1920 | original fields to optimize |
| ``deltatech_image_optimize.webp_quality`` | 85 | WebP quality for transparent images |
| ``deltatech_image_optimize.force_jpeg`` | 0 | ignore alpha, always JPEG — **destructive, see below** |
| ``deltatech_image_optimize.variant_fields`` | image_1024,image_512,image_256,image_128 | resized variants to recompress in place |
| ``deltatech_image_optimize.variant_quality`` | 85 | quality for re-encoding the variants |
| ``deltatech_image_optimize.variant_min_size`` | 20480 | only recompress variants larger than this (bytes) |

### ⚠ ``force_jpeg`` is destructive — probe before enabling it

``force_jpeg=1`` makes the optimizer ignore the alpha channel entirely. JPEG has
no transparency, so every transparent area is **flattened to black**, and the
original is gone: the optimized image is written through the record, so the
previous attachment no longer exists. There is no undo — the images have to be
re-imported from wherever they came from.

Enable it only on a catalog you have *verified* has no real transparency. "The
originals are stored elsewhere" is not that verification: it covers resolution,
not the alpha channel. A catalog that looks like solid white product shots can
still be a third transparent PNGs — this is what happened on a real deployment,
where 32% of a 40-image sample turned out to have real alpha.

Probe it first, without writing anything (``_dt_image_recompress`` is a pure
function — it returns the bytes and the chosen format, and touches nothing):

```python
A = env["ir.attachment"].sudo()
counts = {}
for att in A.search([("res_field", "in", ["image_1920", "image_variant_1920"]),
                     ("mimetype", "=", "image/png"), ("file_size", ">", 51200)], limit=40):
    _data, fmt = A._dt_image_recompress(att.raw, 78, 1280, 85, False)
    counts[fmt] = counts.get(fmt, 0) + 1
print(counts)  # any WEBP/PNG result = images that force_jpeg would destroy
```

Every ``WEBP`` or ``PNG`` in that count is an image with real transparency. If
there is even one, leave ``force_jpeg`` at ``0`` — the module already sends
opaque images to JPEG on its own, so you lose almost nothing by keeping it off.

## Scheduled action

``Image Optimizer: recompress oversized images`` runs daily. It is
**disabled by default** — review the configuration, test on staging, then
enable it.

For a large one-time backlog you can loop the batch method from the shell:

```python
while env["ir.attachment"]._dt_image_optimize_run(limit=200)["scanned"]:
    env.cr.commit()
```
