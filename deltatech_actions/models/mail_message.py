# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.tools import str2bool

_logger = logging.getLogger(__name__)


class MailMessage(models.Model):
    _inherit = "mail.message"

    @api.model
    def cron_clean_old_messages_from_settings(self):
        """Entry point used by the cron: reads its parameters from Settings
        (General Settings > Database Cleanup) instead of hardcoded values."""
        icp = self.env["ir.config_parameter"].sudo()
        exclude_models_param = icp.get_param("deltatech_actions.messages_exclude_models", "")
        exclude_models = [m.strip() for m in exclude_models_param.split(",") if m.strip()] or False
        return self.cron_clean_old_messages(
            limit=int(icp.get_param("deltatech_actions.messages_limit", 5000)),
            pattern=icp.get_param("deltatech_actions.messages_pattern", "") or "",
            max_date_days=int(icp.get_param("deltatech_actions.messages_max_date_days", 90)),
            dry_run=str2bool(icp.get_param("deltatech_actions.messages_dry_run", "True")),
            exclude_models=exclude_models,
        )

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
        # mimetype fix
        query = """UPDATE ir_attachment set mimetype='application/xml'
                                    WHERE name='%.xml' and mimetype='text/plain'
                                    """
        self.env.cr.execute(query)
        _logger.info("Corrected attachments mimetype.")

        if not max_date_days:
            max_date = datetime.now() - relativedelta(days=1)
        else:
            max_date = datetime.now() - relativedelta(days=max_date_days)
        if not pattern:
            query = """SELECT id FROM mail_message
                                        WHERE NOT (model like any(%(exclude_models)s))
                                        AND create_date <= %(create_date)s
                                        ORDER BY id
                                        limit %(limit)s;
                                        """
            params = {"limit": limit, "create_date": max_date, "exclude_models": exclude_models}
        else:
            query = """SELECT id FROM mail_message
                                WHERE NOT (model like any(%(exclude_models)s))
                                AND create_date <= %(create_date)s AND subject like %(pattern)s
                                ORDER BY id
                                limit %(limit)s;
                                """
            params = {"limit": limit, "create_date": max_date, "pattern": pattern, "exclude_models": exclude_models}

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
