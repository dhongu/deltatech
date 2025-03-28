# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model
    def cron_clean_old_messages(self, limit=100, pattern="", max_date_days=False, dry_run=False, exclude_models=False):
        """
        Delete old messages and linked attachments
        :param limit: limit of messages to delete
        :param pattern: optional pattern of message subject, ex "Facturx%"
        :param max_date_days: relative days from which the messages will be deleted.
        Ex. 30 = messages will be deleted if older than today - 30 days
        :param dry_run: if set to True, just selects the messages and does not delete anything
        :param exclude_models: list of models to exclude. Ex: ["business.%", "res.partner"]
        :return: None
        """

        if not max_date_days:
            max_date = datetime.now() - relativedelta(days=1)
        else:
            max_date = datetime.now() - relativedelta(days=max_date_days)
        if not pattern:
            pattern = "%%"
        query = """SELECT id FROM mail_message
                    WHERE model not in %(exclude_models)s
                    AND create_date <= %(create_date)s AND subject like %(pattern)s
                    ORDER BY id
                    limit %(limit)s;
                    """
        params = {"limit": limit, "create_date": max_date, "pattern": pattern, "exclude_models": tuple(exclude_models)}
        self.env.cr.execute(query, params=params)
        res = self.env.cr.fetchall()
        message_ids = [item[0] for item in res]
        messages_to_delete = self.browse(message_ids)
        all_attachments = messages_to_delete.attachment_ids
        attachments_to_delete = self.env["ir.attachment"]
        # avoid deleting anaf attachments
        for attachment in all_attachments:
            if attachment.mimetype not in ["application/xml", "application/zip", "text/plain"]:
                attachments_to_delete |= attachment
        if not dry_run:
            try:
                attachments_to_delete.sudo().unlink()
                messages_to_delete.sudo().unlink()
            except Exception as e:
                _logger.info(e)
        _logger.info(f"Deleted {len(messages_to_delete)} messages and {len(attachments_to_delete)} attachments linked.")
