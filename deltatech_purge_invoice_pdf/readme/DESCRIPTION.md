# Purge Invoice PDF Attachments

Deletes the PDF attachments Odoo generates automatically for invoices and
credit notes (``account.move``), to reclaim filestore space on an instance
with a long invoicing history — typically a staging/test copy, not
production. The PDF is trivial to regenerate on demand (Print → the same
QWeb report), so keeping years of cached copies around only costs disk.

An attachment is only purged when it matches one of the two signals Odoo
itself uses to identify a cached report PDF:

- it is the move's ``message_main_attachment_id`` — the mechanism current
  Odoo versions use to cache the invoice PDF;
- its filename starts with the move's own ``name`` (with ``/`` replaced by
  ``_``) — the older convention
  ``ir.actions.report.retrieve_attachment`` matches on, still hit by
  reprints or invoices predating that field.

A PDF uploaded manually to the chatter (a scanned document, a signed copy)
keeps its own filename and never matches either signal, so it is left
untouched.

Deletion goes through the ORM's ``ir.attachment.unlink()``, never through the
filesystem directly, so the checksum-based deduplication Odoo relies on is
respected: a physical file is only removed once no attachment references it
any more. The filestore garbage collector (``_gc_file_store()``) runs
immediately afterwards, so the disk space is reclaimed in the same call —
no separate shell step needed.

## Trigger

No wizard, no menu entry — this is a technical maintenance tool:

- **Server action** ``Purge invoice PDF attachments``, runnable on demand
  from *Settings → Technical → Server Actions*.
- **Scheduled action** ``Purge Invoice PDF: delete auto-generated PDF
  attachments``, weekly, **disabled by default** — enable it only on an
  instance where PDFs should never be kept for long (e.g. a staging copy
  refreshed regularly from production).
