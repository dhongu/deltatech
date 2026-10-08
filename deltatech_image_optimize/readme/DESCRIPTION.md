Clean, light product images for the eCommerce catalog, in three jobs on the same images:

- **Remove the background** of product photos: the product is cut out and saved on a
  transparent background (or a solid color), with a before / after preview so the result is
  checked before anything is written.
- **Remove duplicated images**: the same picture stored twice in a product's gallery is found and
  deleted; a picture shared by several products is reported, never deleted.
- **Recompress oversized images**: originals are downscaled and re-encoded (JPEG, or WebP when they
  have transparency), so the filestore and every shop page get lighter.

Everything runs on the Odoo server: no image is sent to an external service.

## Background removal

Product photos taken on a printed mat, on a table or on a supplier's white background end up
looking the same in the shop once the background is gone. Select products in a list and use
**Actions → Remove Image Background**; on a product the action also covers its eCommerce gallery.

**The original image is not kept** — keeping a copy of every image would double the images in the
database. The check therefore happens *before* anything is written, in a wizard:

- up to ``bg_sync_limit`` images (default 5, main and gallery images counted), the wizard shows
  each image **before and after**, on a checkerboard so leftovers are visible. Untick the ones that
  were not cut out well, then **Apply**;
- a larger selection is **queued** for a scheduled action, which processes it in batches. Try a few
  images first;
- the result is saved as WebP, resized variants included.

### How the product is cut out

| Method | Used for | How |
| --- | --- | --- |
| **Uniform background** | photos on white or studio grey | no AI model: the background is what has the color of the image border and touches it. Dark accessories next to the product (a funnel beside a bottle) stay whole, white areas inside the product (a label) stay opaque |
| **AI model** | photos on a real background | a local segmentation model ([rembg](https://github.com/danielgatis/rembg), ISNet by default) |
| **Automatic** (default) | any photo | uniform background when the image border has one color, the AI model otherwise |

After the cut-out, the specks left next to the product are removed.

An AI model tends to keep only the main object and to lose accessories or thin parts. When it works
on a plain background, its result is compared with the color cut-out: if part of the product is
missing, the image is flagged and **unticked** in the wizard. The method and the model can be
changed in the wizard and the preview refreshed.

The AI model needs the optional Python library ``rembg`` on the server (see Configuration). Without
it, photos on a plain background are still cut out by color.

Check the marketplaces and feeds the images are sent to before converting a whole catalog: some
accept only JPEG or PNG, and show a transparent image on a black background. A solid white
background can be chosen instead.

## Duplicated product images

Finds product gallery images whose content is **byte-identical**, from the checksum Odoo already
computes for every image: the whole catalog is scanned with one indexed query, without decoding a
single image.

Two images with the same checksum are not automatically redundant:

| Situation | Meaning | Action |
| --- | --- | --- |
| The same picture **twice on one product** | a genuine duplicate: the gallery shows the same thing twice | removed |
| The same picture on **several products** | usually a supplier feed shipping one generic photo for a whole range | **never removed** — each product needs its own copy |

Both happen at once, and at scale. On a real catalog of 69 761 product images (19 959 distinct
contents), **17 821 — 25.5% — were redundant inside a single product**, while 1 204 contents were
legitimately shared across products.

**Duplicated Images** lists the groups side by side, so the cross-product case stays visible as a
data-quality signal. **Remove Duplicated Images** shows exactly what will be deleted, then keeps, in
each group of the same content on the same product, the image the website shows first; images
carrying a video are always kept.

Only identical content is found. The same photo re-exported, resized or recompressed has a different
checksum — on a product re-imported from Shopify, the same 1080×1080 shot came back at 62 KB, 76 KB
and 77 KB. Removing duplicates frees **catalog clutter, not much disk**: Odoo stores one file per
checksum, so the copies already shared a file.

## Recompression

Recompresses oversized **original** product images and then their resized variants:

- downscaled to a maximum side of 1920 pixels;
- photos without transparency re-encoded as progressive **JPEG** (quality 85);
- images with real transparency kept as **WebP** (or optimized PNG when the server has no WebP
  encoder), alpha preserved;
- animated GIFs skipped;
- the result kept only when it is actually smaller.

The new image is written through the product, so Odoo regenerates the resized variants from it.
Processed images are flagged and skipped on the next run; new or changed images are picked up
automatically.

### How much space you actually get back

Odoo stores one file per checksum, so images with identical content share one file, and recompressing
one of them frees nothing while the others still point at it. Each run therefore logs two figures:
the images got lighter by *freed*, and the disk gave back *on disk*. On a real deployment the first
was **29 GB** and the second about **4 GB** — 815 000 image attachments lived in 508 000 files. Quote
the *on disk* figure when someone asks how much space this recovers; the *freed* one is what every
page load saves.

The filestore grows *before* it shrinks: the space comes back once the filestore cleanup runs, at
the end of each scheduled pass.
