## Export Attachments

1. Go to **Settings > Technical > Database Structure > Export attachment**.
2. In the **Domain** field, enter a valid Odoo domain expression to filter which
   attachments should be exported. The default domain
   `[("mimetype","not in",["application/pdf"])]` exports every attachment that is
   not a PDF.
3. Click **Apply**. The wizard searches `ir.attachment` using the domain, bundles
   all files found on disk into a ZIP archive, and transitions to the download step.
4. When the "Export Complete" message appears, click the **File** download button to
   save `ExportOdooAttachment.zip` to your computer.
5. Click **Cancel** to close the wizard.

**Note:** Only attachments that have a physical file on the server (`store_fname`
populated and the file present on disk) are included in the ZIP. Database-stored
attachments (binary stored in the column, not the filestore) are silently skipped.
