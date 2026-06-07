This module allows Odoo administrators to export a selective set of file attachments as a
single ZIP archive. By providing a domain filter on the `ir.attachment` model, you can precisely
choose which files to include — for example, only attachments of a specific MIME type, linked
to specific records, or stored on a particular field.

**Key features:**

- Export attachments filtered by any Odoo domain expression (MIME type, related model, field name, etc.).
- All matching files are bundled into a single downloadable ZIP archive.
- The ZIP preserves the internal storage path of each file (`store_fname`), making it
  suitable for off-system backups or migration scenarios.
- Only files physically present on disk (`store_fname` set and path exists) are included,
  avoiding broken references.

**Example domains:**

- `[("mimetype","not in",["image/png","image/jpeg","application/pdf"])]` — export all
  attachments that are not common images or PDFs.
- `[("res_model","not ilike","product"),("res_model","!=","export.attachment"),("res_field","like","%")]`
  — export attachments linked to fields (not products or the wizard itself).
