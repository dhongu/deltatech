# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.model
    def cron_clean_xml_attachments(self, limit=10, duplicates=10):
        """
        Searches for duplicate xml attachments for invoices and deletes them (mainly edi ubl)
        :param limit: how many invoices with duplicate attachments should be processed.
        Increase this number if you have many invoices with few duplicate attachments
        Decrease this number if you have few invoices with many duplicates attachments
        :param duplicates: how many attachments with same name are found
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
                        attachments.unlink()
                    except Exception as e:
                        _logger.info(f"Cannot delete attachments: {e}")

        _logger.info(f"Deleted {total_attachments} attachments.")
