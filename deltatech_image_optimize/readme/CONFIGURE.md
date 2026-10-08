The module works with its defaults. Everything below is tuned in *Settings → Technical →
Parameters → System Parameters* (developer mode), keys prefixed with ``deltatech_image_optimize.``.

## Background removal

**The rembg library**, for photos on a real background. Photos on a plain background are cut out
by color without it. [rembg](https://github.com/danielgatis/rembg) is a local segmentation model on
ONNX Runtime; it is an optional dependency, not declared in the manifest, so the module installs
without it. Add it to the ``requirements.txt`` of the deployment (on odoo.sh, in the project
repository) and rebuild:

```
rembg[cpu]
```

The model is downloaded on first use (ISNet: 180 MB, under ``~/.rembg/models`` or ``$U2NET_HOME``)
and kept loaded per worker process; on CPU an image takes about one second. Only one model is kept
loaded at a time.

![System parameters for background removal](https://apps.odoocdn.com/apps/assets/19.0/deltatech_image_optimize/image_optimize_system_parameters.png)

| Key | Default | Meaning |
| --- | --- | --- |
| ``bg_method`` | auto | ``auto``, ``uniform`` (by color, no AI model) or ``rembg`` (always the AI model) |
| ``bg_model`` | isnet-general-use | rembg model. ``birefnet-general`` is finer but about 10× slower, 970 MB, and does not fit in the memory of an odoo.sh worker |
| ``bg_tolerance`` | 24 | how far (0..255 per channel) a pixel may be from the border color and still be background; raise it for noisy JPEGs or soft shadows |
| ``bg_min_island`` | 1 | pieces smaller than this percent of the main object are removed; 0 = keep all |
| ``bg_lost_warning`` | 5 | flag and untick an image when the AI model left out this percent of a product on a plain background |
| ``bg_crop`` | 0 | 1 = frame the product in a square, 0 = keep the original canvas |
| ``bg_margin`` | 5 | margin around the product, in percent, when cropping |
| ``bg_color`` | (empty) | empty = transparent (WebP); a color such as ``#FFFFFF`` = solid background (JPEG) |
| ``bg_sync_limit`` | 5 | up to this many images (main and gallery) get a preview; more are queued |
| ``bg_batch`` | 20 | images per run of the scheduled action |

**Access rights.** The action needs *Products: Create*. Writing gallery images needs *Sales:
Administrator* or *Website: Restricted Editor*, as in standard Odoo.

## Recompression

| Key | Default | Meaning |
| --- | --- | --- |
| ``quality`` | 85 | JPEG quality (1..95) |
| ``max_dim`` | 1920 | max side in pixels |
| ``min_size`` | 102400 | only originals larger than this (bytes) |
| ``batch`` | 50 | images per run |
| ``flush_every`` | 20 | flush and drop the ORM cache every N images; lower it for very large images |
| ``target_fields`` | image_1920,image_variant_1920 | original fields to optimize |
| ``webp_quality`` | 85 | WebP quality for transparent images |
| ``variant_fields`` | image_1024,image_512,image_256,image_128 | resized variants recompressed in place |
| ``variant_quality`` | 85 | quality for re-encoding the variants |
| ``variant_min_size`` | 20480 | only recompress variants larger than this (bytes) |
| ``force_jpeg`` | 0 | ignore alpha, always JPEG — **destructive, see below** |

The scheduled action **Image Optimizer: recompress oversized images** runs daily and is **disabled
by default**: review the parameters, run it manually on staging, then enable it. Its state survives
module upgrades.

For a large one-time backlog, loop the batch method from the shell:

```python
while env["ir.attachment"]._dt_image_optimize_run(limit=200)["scanned"]:
    env.cr.commit()
```

### ``force_jpeg`` is destructive — probe before enabling it

``force_jpeg=1`` makes the optimizer ignore the alpha channel. JPEG has no transparency, so every
transparent area is **flattened to black**, and the original is gone: there is no undo, the images
have to be re-imported.

Enable it only on a catalog *verified* to have no real transparency. "The originals are stored
elsewhere" is not that verification: it covers resolution, not the alpha channel. On a real
deployment, 32% of a 40-image sample of a catalog believed to be plain white shots had real alpha.

Probe first, without writing anything (``_dt_image_recompress`` returns the bytes and the chosen
format and touches nothing):

```python
A = env["ir.attachment"].sudo()
counts = {}
for att in A.search([("res_field", "in", ["image_1920", "image_variant_1920"]),
                     ("mimetype", "=", "image/png"), ("file_size", ">", 51200)], limit=40):
    _data, fmt = A._dt_image_recompress(att.raw, 78, 1280, 85, False)
    counts[fmt] = counts.get(fmt, 0) + 1
print(counts)  # any WEBP/PNG result = images that force_jpeg would destroy
```

Every ``WEBP`` or ``PNG`` in that count is an image with real transparency. If there is even one,
leave ``force_jpeg`` at ``0``: opaque images already go to JPEG on their own.

To measure the real image occupancy of the whole database (one file per checksum):

```sql
SELECT pg_size_pretty(sum(sz)) FROM (
    SELECT DISTINCT ON (checksum) file_size AS sz
    FROM ir_attachment WHERE res_field IS NOT NULL AND checksum IS NOT NULL
    ORDER BY checksum, id
) t;
```

## Duplicated images

The menus **Duplicated Images** and **Remove Duplicated Images** (Website → eCommerce → Products)
are for administrators. On install, a hook fills the image checksum of the existing gallery images
with one SQL update; to refresh it later from the shell:

```python
env["product.image"]._dedup_backfill_checksums()
```
