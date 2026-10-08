# Image Optimizer

Three related jobs on the same images: **recompress** them to reclaim filestore
space, **remove the ones stored twice**, and **remove the background** of product
photos.

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

## Product image background removal

Product photos taken on a printed mat or a cluttered table can have their
background removed: the product is cut out and saved on a **transparent
background as WebP**, the format the optimizer already uses for transparent
images.

Select products (or product images) in a list and use
**Action → Remove Image Background**. On a product the action also covers the
extra images of its eCommerce gallery.

**The original image is not kept.** Keeping a copy of every image would double
the images in the database, so the check happens *before* anything is written,
in a wizard:

- Up to ``bg_sync_limit`` images (default 5), the wizard shows each image
  **before and after**. Untick the ones where the product was not cut out well,
  then **Apply**. Only the ticked images are written; the preview itself lives
  in the wizard and disappears with it.
- A larger selection is too slow to preview. The wizard asks for confirmation
  and **queues** the images for the scheduled action
  ``Image Optimizer: remove product image background``, which processes them in
  batches of ``bg_batch``, committing after every image. Try a few images first.
- The cut-out is written as PNG through the record, so Odoo generates the
  resized variants, and then each attachment is re-encoded to WebP in place:
  Odoo does not resize WebP, so writing a WebP through the field would leave
  every variant at full size.
- When the model finds no object in an image, it is left untouched: unticked in
  the preview, marked *Failed* (``bg_removal_state = error``) in the queue.

### How the product is cut out

| Method (``bg_method``) | When | What it does |
| --- | --- | --- |
| ``uniform`` | photo on a plain background (white, studio grey) | no AI model: the background is what has the color of the image border and touches it; dark accessories next to the product are kept, white areas inside the product stay |
| ``rembg`` | photo on a real background | the AI model ``bg_model`` |
| ``auto`` (default) | any | ``uniform`` when at least 90% of the image border has one color, otherwise ``rembg`` |

After the cut-out, pieces smaller than ``bg_min_island`` percent of the main
object are removed — the specks a model leaves next to the product.

The AI model tends to keep only the main object: on a bottle with a funnel
beside it, the funnel is cut away or broken in pieces. When the model works on
a plain background, its result is compared with the color cut-out; if it left
out at least ``bg_lost_warning`` percent of the product, the line gets a
warning and is **unticked**.

In the wizard, the method and the AI model can be changed and the preview
refreshed; the result is shown on a checkerboard, so the transparent parts and
any leftovers are visible. The queue always uses the system parameters.

### Requirement for photos on a real background: the rembg library

The cut-out is done by [rembg](https://github.com/danielgatis/rembg), a local
segmentation model on ONNX Runtime — images are not sent to any external
service. It is an **optional** dependency, not declared in the manifest, so the
module still installs where it is missing; images on a plain background are then
cut out by color, and the others say in the wizard what to add.
Add it to the ``requirements.txt`` of the deployment:

```
rembg[cpu]
```

The model is downloaded on first use (``isnet-general-use``: 180 MB, under
``~/.rembg/models``, or ``$U2NET_HOME``) and kept loaded per worker process, which needs about 1 GB of RAM
while it runs. On CPU an image takes about one second.

| Key | Default | Meaning |
| --- | --- | --- |
| ``deltatech_image_optimize.bg_method`` | auto | ``auto``, ``uniform`` (by color, no AI model) or ``rembg`` (AI model) |
| ``deltatech_image_optimize.bg_tolerance`` | 24 | how far (0..255 per channel) a pixel may be from the border color and still be background; raise it for noisy JPEGs or soft shadows |
| ``deltatech_image_optimize.bg_min_island`` | 1 | pieces smaller than this percent of the main object are removed; 0 = keep all |
| ``deltatech_image_optimize.bg_lost_warning`` | 5 | warn and untick when the AI model left out this percent of a product on a plain background |
| ``deltatech_image_optimize.bg_model`` | isnet-general-use | rembg model; ``birefnet-general`` is finer but ~10x slower, 970 MB, and does not fit in the memory of an odoo.sh worker |
| ``deltatech_image_optimize.bg_crop`` | 0 | 1 = frame the product in a square, 0 = keep the original canvas |
| ``deltatech_image_optimize.bg_margin`` | 5 | margin around the product, in percent, when cropping |
| ``deltatech_image_optimize.bg_color`` | (empty) | empty = transparent; a color such as ``#FFFFFF`` = solid background |
| ``deltatech_image_optimize.bg_sync_limit`` | 5 | up to this many images get a preview; more are queued |
| ``deltatech_image_optimize.bg_batch`` | 20 | images per scheduled run |

Check the marketplaces and feeds the images are sent to before converting a
whole catalog: some accept only JPEG or PNG, and a transparent image may be
shown on a black background there.

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
