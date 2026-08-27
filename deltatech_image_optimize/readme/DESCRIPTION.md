# Image Optimizer

Two related jobs on the same images: **recompress** them to reclaim filestore
space, and **remove the ones stored twice**.

## Recompression

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


## Duplicated product images

Finds `product.image` records whose content is **byte-identical** and removes the
redundant ones. Odoo already computes a SHA1 checksum for every image attachment
when it is written, so this reads that value instead of decoding images — the
whole catalog is scanned with one indexed query.

### The distinction that matters

Two images with the same checksum are not automatically redundant:

| Situation | Meaning | Action |
| --- | --- | --- |
| The same picture appears **twice on one product** | A genuine duplicate — the gallery shows the same thing twice. | Safe to remove. |
| The same picture appears on **several products** | Usually a supplier feed shipping one generic photo for a whole range. | **Never removed** — each product needs its own copy, or it ends up with no image. |

Both happen at once, and at scale. On a real catalog of 69 761 product images
(19 959 distinct contents), **17 821 — 25.5% — were redundant inside a single
product**, while 1 204 contents were legitimately shared across products. One
single photo appeared 1 204 times over 565 products: 565 of those must stay.

The wizard removes only the first kind. In each group of *(content, product,
variant)* it keeps the image that comes first by `sequence, id` — the one the
website shows first anyway — and deletes the rest. Records carrying a
`video_url` are always kept, since the video is not a duplicate.

The report shows both figures side by side, so the cross-product case stays
visible as a data-quality signal instead of being silently deleted.

### What it does not find

Only identical content. The same photo re-exported, resized or recompressed has
a different checksum and is reported as distinct — and this is not a corner
case. On a product re-imported from Shopify in three passes, 22 images held only
10 distinct pictures, yet the checksum matched on just one pair: the same
1080×1080 shot came back at 62 KB, 76 KB and 77 KB because the source
re-encoded it every time. Catching those needs perceptual hashing, which
decodes every image and needs a similarity threshold.

### Space

Removing duplicates frees **catalog clutter, not much disk**. Odoo stores one
file per checksum, so the copies already shared a single file; deleting them
drops the `ir_attachment` rows. Use the recompression above for actual filestore
savings.

### Usage

Website → Configuration → eCommerce → Products → **Duplicated Images**

The list opens filtered on the removable groups. Select the ones you want and
use **Remove Duplicated Images**, which shows exactly what will be deleted
before it deletes anything. The same menu entry run without a selection works on
the whole catalog.

On install, the hook fills `image_checksum` with a single SQL `UPDATE` from
`ir_attachment`. Computing it through the ORM would read every image out of the
filestore. To refresh it later from the shell:

```python
env["product.image"]._dedup_backfill_checksums()
```

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
