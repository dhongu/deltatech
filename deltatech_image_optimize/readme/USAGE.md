This module has no menus or views — it works entirely through system parameters and a scheduled action.

1. Go to **Settings > Technical > System Parameters** (developer mode) and adjust as needed:
   - `deltatech_image_optimize.quality` — JPEG quality, 1-95 (default 85).
   - `deltatech_image_optimize.max_dim` — maximum side in pixels for the resized image (default 1920).
   - `deltatech_image_optimize.min_size` — only attachments larger than this size in bytes are processed (default 102400).
   - `deltatech_image_optimize.batch` — number of images processed per cron run (default 1000).
   - `deltatech_image_optimize.target_fields` — comma-separated field names to optimize (default `image_1920,image_variant_1920`).
2. Go to **Settings > Technical > Automation > Scheduled Actions** and enable **Image Optimizer: recompress oversized images**. It ships **disabled by default** — review the configuration and test on staging before enabling it in production.
3. Once enabled, the cron downscales oversized originals, re-encodes photos as progressive JPEG (or keeps PNG when transparency is present), skips animated GIFs, and only keeps the result if it is actually smaller. Odoo regenerates the smaller `image_1024/512/256/128` variants automatically. Processed attachments are flagged (`deltatech_image_optimized`) so they are not reprocessed; new or changed images are picked up on the next run.
4. To clear a large existing backlog in one go, run this from the Odoo shell instead of waiting for daily cron batches:
   ```python
   while env["ir.attachment"]._dt_image_optimize_run(limit=200)["scanned"]:
       env.cr.commit()
   ```
