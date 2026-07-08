This is a technical utility module with no menus or settings — it runs in the background and exposes a couple of maintenance helpers for developers/administrators:

- Deleting a website-specific view (`ir.ui.view`) now also deletes its inherited child views, avoiding orphaned view records when cleaning up website pages.
- Attachments (`ir.attachment`) get a stored filename and a computed file size field, useful for auditing filestore usage from the Attachments list/pivot view.
- To reclaim disk space from orphaned filestore files, an administrator can call `env['ir.attachment'].check_filestore()` from the Odoo shell (or a server action) to list unreferenced files, and `check_filestore(delete=True)` to actually remove them. Use with care — this deletes files from the filestore, not just database records.
