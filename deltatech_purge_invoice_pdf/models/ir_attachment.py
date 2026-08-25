import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def _dt_purge_invoice_pdf_target_ids(self):
        """Auto-generated invoice PDF attachments, safe to delete.

        Two independent signals, either one qualifies an attachment:

        - it is the move's ``message_main_attachment_id`` (the mechanism
          Odoo itself uses to cache the invoice PDF since the
          ``message_main_attachment_id`` field was introduced);
        - its ``name`` starts with the move's own ``name`` (with ``/``
          replaced by ``_``), the older convention
          ``ir.actions.report.retrieve_attachment`` matches on, still hit by
          reprints or invoices older than that field.

        A PDF manually uploaded to the chatter keeps its own filename, so it
        never matches either signal and is left untouched.
        """
        candidates = self.search(
            [
                ("res_model", "=", "account.move"),
                ("mimetype", "=", "application/pdf"),
            ]
        )
        if not candidates:
            return candidates.ids

        moves = self.env["account.move"].browse(candidates.mapped("res_id")).exists()
        move_by_id = {move.id: move for move in moves}

        target_ids = []
        for attachment in candidates:
            move = move_by_id.get(attachment.res_id)
            if not move:
                continue
            if attachment.id == move.message_main_attachment_id.id:
                target_ids.append(attachment.id)
                continue
            expected_prefix = (move.name or "").replace("/", "_")
            if expected_prefix and attachment.name and attachment.name.startswith(expected_prefix):
                target_ids.append(attachment.id)
        return target_ids

    @api.model
    def _dt_purge_invoice_pdf_run(self):
        """Delete the invoice PDF attachments found by
        :meth:`_dt_purge_invoice_pdf_target_ids` and reclaim their filestore
        space immediately.

        Uses ``unlink()`` (never touches the filesystem directly), so the
        checksum-based deduplication is respected: a physical file is only
        removed once no attachment references it any more. Returns the
        number of attachment rows deleted.
        """
        target_ids = self._dt_purge_invoice_pdf_target_ids()
        count = len(target_ids)
        if count:
            self.browse(target_ids).unlink()
            self._gc_file_store()
        _logger.info("purge_invoice_pdf: %s attachment(s) deleted, filestore GC run", count)
        return count
