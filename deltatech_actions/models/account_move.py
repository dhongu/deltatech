# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.tools import str2bool

from .cleanup_summary import autovacuum_run, log_prefix, rows_summary

PREFIX = "deltatech_actions."

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def cron_clean_xml_attachments_from_settings(self):
        """Entry point used by the cron: reads its parameters from Settings
        (General Settings > Database Cleanup) instead of hardcoded values."""
        icp = self.env["ir.config_parameter"].sudo()
        return self.cron_clean_xml_attachments(
            limit=int(icp.get_param("deltatech_actions.xml_limit", 10)),
            duplicates=int(icp.get_param("deltatech_actions.xml_duplicates", 10)),
            max_attachments_to_delete=int(icp.get_param("deltatech_actions.xml_max_delete", 50)),
            dry_run=str2bool(icp.get_param("deltatech_actions.xml_dry_run", "True")),
            max_date_days=int(icp.get_param("deltatech_actions.xml_max_date_days", 30)),
        )

    @api.autovacuum
    def _gc_generated_pdfs(self):
        """Run the invoice PDF cleanup from the autovacuum job -- see autovacuum_run()."""
        return autovacuum_run(self, "cron_clean_generated_pdfs_from_settings", PREFIX + "invoice_pdf_limit")

    @api.model
    def cron_clean_generated_pdfs_from_settings(self):
        """Entry point used by the cron: reads its parameters from Settings
        (General Settings > Database Cleanup) instead of hardcoded values."""
        icp = self.env["ir.config_parameter"].sudo()
        dry_run = str2bool(icp.get_param("deltatech_actions.invoice_pdf_dry_run", "True"))
        rows = self.cron_clean_generated_pdfs(
            limit=int(icp.get_param("deltatech_actions.invoice_pdf_limit", 5000)),
            pattern=icp.get_param("deltatech_actions.invoice_pdf_pattern", "") or "",
            max_date_days=int(icp.get_param("deltatech_actions.invoice_pdf_max_date_days", 90)),
            dry_run=dry_run,
        )
        return rows_summary(rows, dry_run)

    @api.model
    def cron_clean_xml_attachments(
        self, limit=10, duplicates=10, max_attachments_to_delete=50, dry_run=False, max_date_days=False
    ):
        """
        Searches for duplicate xml attachments for invoices and deletes them (mainly edi ubl)
        :param limit: how many invoices with duplicate attachments should be processed.
        Increase this number if you have many invoices with few duplicate attachments
        Decrease this number if you have few invoices with many duplicates attachments
        :param duplicates: how many attachments with same name are found
        :param max_attachments_to_delete: maximum attachment number to delete
        :param dry_run: if set to True, just selects the attachments and does not delete anything
        :param max_date_days: only consider attachments older than this many days. Ex. 30 =
        an attachment created today is never touched even if it duplicates an older one.
        Falsy = no age filter, kept for backwards compatibility.
        :return: None
        """
        max_date = datetime.now() - relativedelta(days=max_date_days) if max_date_days else None
        date_clause = "AND create_date <= %(create_date)s" if max_date else ""

        query = f"""SELECT name, count(name) as count_name
        FROM ir_attachment
        WHERE mimetype='application/xml' AND res_model='account.move'
        {date_clause}
        GROUP BY name
        HAVING COUNT(name) > %(duplicates)s limit %(limit)s;
        """
        params = {"limit": limit, "duplicates": duplicates, "create_date": max_date}
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        counter = 1
        att_count = len(res)
        total_attachments = 0
        for attachment_name in res:
            domain = [("name", "=", attachment_name[0])]
            if max_date:
                domain.append(("create_date", "<=", max_date))
            attachments = self.env["ir.attachment"].search(domain)
            if attachments:
                counter += 1
                invoice_id = self.browse(attachments[0].res_id)
                linked_attachments = invoice_id.edi_document_ids.attachment_id
                attachments -= linked_attachments
                if attachments:
                    if len(attachments) > max_attachments_to_delete:
                        attachments = attachments[:max_attachments_to_delete]
                    total_attachments += len(attachments)
                    _logger.info(
                        f"{log_prefix(dry_run)} attachments: {attachment_name[0]} "
                        f"({counter}/{att_count} - {len(attachments)} attachments)"
                    )
                    if not dry_run:
                        try:
                            attachments.sudo().unlink()
                        except Exception as e:
                            _logger.info(f"Cannot delete attachments: {e}")

        _logger.info(f"{log_prefix(dry_run)} {total_attachments} attachments.")
        return {"count": total_attachments, "size": None, "dry_run": dry_run}

    @api.model
    def cron_clean_generated_pdfs(self, limit=100, pattern="", max_date_days=False, dry_run=False):
        """
        Delete generated pdf from invoices
        :param limit: limit of attachments to delete
        :param pattern: the beginning of the attachment name to delete
        :param max_date_days: relative days from which the attachments will be deleted.
        Ex. 30 = attachments will be deleted if older than today - 30 days
        :param dry_run: if set to True, just selects the attachments and does not delete anything
        :return: None

        Sending an invoice by email attaches its PDF to the outgoing
        mail.message, not to the move (res_model='mail.message', with the
        message itself pointing at the move) -- measured on a real
        deployment, that is where the overwhelming majority of invoice PDFs
        actually live (40k+, ~1.9 GB, against a handful directly on
        account.move), and every resend leaves its own copy behind. Both
        owners are searched here.
        """
        if not max_date_days:
            max_date = datetime.now() - relativedelta(days=1)
        else:
            max_date = datetime.now() - relativedelta(days=max_date_days)
        if not pattern:
            pattern = "%%"
        query = """SELECT att.id, att.file_size FROM ir_attachment att
                    LEFT JOIN mail_message msg ON att.res_model = 'mail.message' AND att.res_id = msg.id
                    WHERE att.mimetype = 'application/pdf'
                    AND (att.res_model = 'account.move' OR msg.model = 'account.move')
                    AND att.create_date <= %(create_date)s AND att.name like %(pattern)s
                    limit %(limit)s;
                    """
        params = {"limit": limit, "create_date": max_date, "pattern": pattern}
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        attachment_ids = [item[0] for item in res]
        # `or 0`: ir_attachment.file_size is nullable, and a single NULL row used to
        # raise TypeError here. Inside the autovacuum job that failure is invisible --
        # _run_vacuum_cleaner logs the exception, rolls the transaction back and moves
        # on, so a crashing cleanup looks exactly like one with nothing to delete.
        sum_sizes = sum((item[1] or 0) for item in res)
        if not dry_run:
            attachments = self.env["ir.attachment"].browse(attachment_ids)
            try:
                attachments.sudo().unlink()
            except Exception as e:
                _logger.info(e)
        _logger.info(
            f"{log_prefix(dry_run)} {len(attachment_ids)} attachments, "
            f"total size: {round(sum_sizes / (1024 * 1024), 3)} MB"
        )
        return res
