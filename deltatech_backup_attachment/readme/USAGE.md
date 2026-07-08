1. Open the **Export Attachment** wizard (Settings > Technical > or the menu added by this module).
2. Enter a domain filter to select which `ir.attachment` records to back up, for example to exclude images/PDFs and keep everything else:

   `[("mimetype","not in",["image/png", "image/jpeg","application/pdf"])]`

   or to exclude product-related and already-exported attachments:

   `[('res_model','not ilike','product'),('res_model','!=','export.attachment'),('res_field','like','%')]`
3. Click **Export** — the matching attachments (that exist on disk) are collected into a ZIP archive.
4. Download the generated ZIP file from the wizard once it's ready.
