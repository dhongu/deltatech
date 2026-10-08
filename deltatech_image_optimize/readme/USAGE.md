Before you start, see *Configuration* for the optional AI library and the system parameters.

The module covers three flows on the same product images: **Remove background**,
**Duplicated images** and **Recompression**.

> **Important:** the original image is **not kept**, neither when the background is removed nor
> when images are recompressed. Always check the preview before applying.

## Remove background

**Step 1 — Select the products and start the action**

Go to *Website → eCommerce → Products → Products* and switch to list view. Tick the products whose
photos you want to clean, then choose **Actions → Remove Image Background**. On a product, the action
also covers the images of its eCommerce gallery.

Access rights: the action needs the **Products: Create** right. To modify gallery images you also
need **Sales: Administrator** or **Website: Restricted Editor**; without them **Apply** stops with an
access error.

![Remove Image Background action on the product list](https://apps.odoocdn.com/apps/assets/19.0/deltatech_image_optimize/image_optimize_product_action.png)

**Step 2 — Check the preview**

When the selection has at most `bg_sync_limit` images (default 5), the wizard cuts them out on the
spot, writes nothing yet, and shows **Before** and **After** for each one. The limit counts
**images**, not products: the main image plus every gallery image of each product.

- Each row is one image: *main image* is the product's main picture, *gallery image N* is the N-th
  picture of its gallery. The *After* column shows the result on a checkerboard; the squares are the
  transparent area.
- Check that the product is complete (accessories, cap, funnel), that nothing is left around it and
  that white areas inside the product (the label) stayed opaque.
- Untick the rows whose result is not good and press **Apply**. Only ticked rows are written.

With the *Automatic* method, the wizard cuts by color when the image border has a single color and
uses the AI model otherwise.

![Preview with the automatic method](https://apps.odoocdn.com/apps/assets/19.0/deltatech_image_optimize/image_optimize_preview_automatic.png)

**Step 3 — When the AI model loses part of the product**

When the AI model is used on a photo with a uniform background, its result is compared with the
cut-out by color. If it left out at least `bg_lost_warning` percent of the product, the row shows a
warning in the *Warning* column and is **unticked**.

Choose another *Method* or *AI Model* and press **Refresh Preview**. Refresh rebuilds the preview
**and also the ticks**. So first choose the method and press **Refresh Preview**, and only then
untick what is not good, right before **Apply**.

![Warning: the AI model lost the funnel](https://apps.odoocdn.com/apps/assets/19.0/deltatech_image_optimize/image_optimize_ai_warning.png)

**Step 4 — The result on the product**

After **Apply**, the product image (and its resized variants) is saved on a transparent background,
in WebP format (PNG if the server cannot encode WebP; JPEG if a solid `bg_color` is set). The
*Background Removal* status becomes *Removed*. On the shop, the product appears on the page background.

![Product after background removal](https://apps.odoocdn.com/apps/assets/19.0/deltatech_image_optimize/image_optimize_product_after.png)

**Step 5 — Many images: the queue**

Above `bg_sync_limit` images, a live preview would take too long. The wizard only asks for
confirmation and sends the images to the **Queue**. The scheduled action *Image Optimizer: remove
product image background* processes them in batches of `bg_batch`, using the method from the system
parameters. An image that cannot be cut out stays unchanged and is marked *Failed*; the reason
appears only in the server log.

To find pending or failed images, use *Filters → Add a custom filter* on the product list, on the
*Background Removal* field (*Pending* or *Failed*).

Tip: try a few images with the preview first, to see the result on your own catalog photos.

![Queue for a large selection](https://apps.odoocdn.com/apps/assets/19.0/deltatech_image_optimize/image_optimize_queue.png)

## Remove a watermark

**Step 6 — Remove the watermark of your catalog images**

Only on images whose watermark you have the right to remove (your own, or with the rights holder's
written consent): the wizard opens with this reminder.

1. In *Website → eCommerce → Products → Products*, list view, tick the products that carry the
   **same** watermark — the more, the better the watermark is learned — and choose
   **Actions → Remove Watermark**.
2. Check the **Detected Watermark**: it is the logo the module found in the images.
3. Check each image before and after; untick the ones that are not good, then **Apply**. Above
   ``wm_sync_limit`` images the selection is queued instead.

## Duplicated images

**Step 7 — Find the duplicates**

*Website → eCommerce → Products → Duplicated Images* (administrator only). The list opens filtered
on the groups that can be cleaned (*Removable*).

- Each row is an image content that is identical byte for byte. *Copies* is how many images have
  this content, *Products* is on how many products, *Removable* is how many copies repeat inside
  the same product.
- *Removable* is lower than *Copies*: one image always remains on each product.
- The *Shared Across Products* filter shows a picture used on several products. It is reported but
  **never deleted**.
- The **Images** button opens the images of the group.

![List of duplicated images](https://apps.odoocdn.com/apps/assets/19.0/deltatech_image_optimize/image_optimize_duplicates_list.png)

**Step 8 — Delete the duplicates**

*Website → eCommerce → Products → Remove Duplicated Images*. The wizard shows how many contents have
copies to delete, how many images will be deleted and kept, and the exact list. From each group
(same content, same product) the image that appears first in the gallery stays; images with a video
always stay. **Remove Duplicates** asks for confirmation and deletes permanently.

![Wizard for removing duplicates](https://apps.odoocdn.com/apps/assets/19.0/deltatech_image_optimize/image_optimize_duplicates_remove.png)

## Recompression

**Step 9 — Recompress oversized images**

Go to *Settings → Technical → Automation → Scheduled Actions* and open *Image Optimizer: recompress
oversized images*. The action is **inactive** after installation. Run it first on a staging
database with **Run Manually**: one run takes the largest `batch` originals (default 50) above
`min_size`, shrinks them to `max_dim` pixels and re-encodes them (JPEG, or WebP when they have
transparency), then recompresses the same number of variants and cleans the filestore. The result
is kept only if it is smaller. Check the products with the largest images, then activate the action
on production.

The parameters are in *Settings → Technical → Parameters → System Parameters* (developer mode),
keys starting with `deltatech_image_optimize.`. Do not change `force_jpeg`: at 1, transparency
becomes black permanently.

![Scheduled action for recompression](https://apps.odoocdn.com/apps/assets/19.0/deltatech_image_optimize/image_optimize_recompress_cron.png)
