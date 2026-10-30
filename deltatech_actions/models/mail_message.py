# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.tools import SQL

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
        :param exclude_models: list of models to exclude. Ex: ["business.%", "res.partner"]; False = none
        :return: None
        """
        # mimetype fix
        self.env.cr.execute(
            SQL(
                "UPDATE ir_attachment SET mimetype = 'application/xml' WHERE name LIKE %s AND mimetype = 'text/plain'",
                "%.xml",
            )
        )
        _logger.info("Corrected attachments mimetype.")

        if not max_date_days:
            max_date = datetime.now() - relativedelta(days=1)
        else:
            max_date = datetime.now() - relativedelta(days=max_date_days)
        # NOT LIKE ALL: the model must match none of the excluded patterns
        # (NOT LIKE ANY kept every message whose model differed from at least one pattern)
        where = SQL(
            "model NOT LIKE ALL(%s::varchar[]) AND create_date <= %s",
            list(exclude_models or []),
            max_date,
        )
        if pattern:
            where = SQL("%s AND subject like %s", where, pattern)

        self.env.cr.execute(SQL("SELECT id FROM mail_message WHERE %s ORDER BY id LIMIT %s", where, limit))
        res = self.env.cr.fetchall()
        message_ids = [item[0] for item in res]
        messages_to_delete = self.browse(message_ids)
        all_attachments = messages_to_delete.attachment_ids
        attachments_to_delete = self.env["ir.attachment"]
        # avoid deleting anaf attachments
        for attachment in all_attachments:
            if attachment.mimetype not in ["application/xml", "application/zip", "text/plain"]:
                attachments_to_delete |= attachment
        done = 0
        if not dry_run and messages_to_delete:
            try:
                with self.env.cr.savepoint():
                    attachments_to_delete.sudo().unlink()
                    messages_to_delete.sudo().unlink()
                done = len(messages_to_delete)
            except Exception as e:
                _logger.info(e)
        _logger.info(
            "Deleted %s messages (%s selected) and %s attachments linked.",
            done,
            len(messages_to_delete),
            len(attachments_to_delete) if done else 0,
        )

        # dry run or failed unlink: nothing advanced, so nothing remains for this run
        remaining = 0
        if done:
            self.env.cr.execute(SQL("SELECT count(*) FROM mail_message WHERE %s", where))
            remaining = self.env.cr.fetchone()[0]
        self.env["ir.cron"]._cron_report_progress(done, remaining)
