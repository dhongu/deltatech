# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def cron_clean_xml_attachments(self, limit=10, duplicates=10, dry_run=False):
        """
        Searches for duplicate xml attachments for invoices and deletes them (mainly edi ubl)
        :param limit: how many invoices with duplicate attachments should be processed.
        Increase this number if you have many invoices with few duplicate attachments
        Decrease this number if you have few invoices with many duplicates attachments
        :param duplicates: how many attachments with same name are found
        :param dry_run: if set to True, just selects the attachments and does not delete anything
        :return: None
        """

        query = """SELECT name, count(name) as count_name
        FROM ir_attachment
        WHERE mimetype='application/xml' AND res_model='account.move'
        GROUP BY name
        HAVING COUNT(name) > %(duplicates)s limit %(limit)s;
        """
        params = {"limit": limit, "duplicates": duplicates}
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        counter = 1
        att_count = len(res)
        total_attachments = 0
        for attachment_name in res:
            attachments = self.env["ir.attachment"].search([("name", "=", attachment_name[0])])
            if attachments:
                counter += 1
                invoice_id = self.browse(attachments[0].res_id)
                linked_attachments = invoice_id.edi_document_ids.attachment_id
                attachments -= linked_attachments
                _logger.info(
                    f"Deleting attachments: {attachment_name[0]} ({counter}/{att_count} - {len(attachments)} attachments to delete)"
                )
                if attachments:
                    try:
                        total_attachments += len(attachments)
                        if not dry_run:
                            attachments.unlink()
                    except Exception as e:
                        _logger.info(f"Cannot delete attachments: {e}")

        _logger.info(f"Deleted {total_attachments} attachments.")

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
        """
        if not max_date_days:
            max_date = datetime.now() - relativedelta(days=1)
        else:
            max_date = datetime.now() - relativedelta(days=max_date_days)
        if not pattern:
            pattern = "%%"
        query = """SELECT id,file_size FROM ir_attachment
                    WHERE mimetype='application/pdf' AND res_model='account.move'
                    AND create_date <= %(create_date)s AND name like %(pattern)s
                    limit %(limit)s;
                    """
        params = {"limit": limit, "create_date": max_date, "pattern": pattern}
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        attachment_ids = [item[0] for item in res]
        sizes = [item[1] for item in res]
        sum_sizes = 0
        for size in sizes:
            sum_sizes += size
        if not dry_run:
            attachments = self.env["ir.attachment"].browse(attachment_ids)
            try:
                attachments.sudo().unlink()
            except Exception as e:
                _logger.info(e)
        _logger.info(
            f"Deleted {len(attachment_ids)} attachments., total size: {round(sum_sizes / (1024 * 1024), 3)} MB"
        )
        return res
