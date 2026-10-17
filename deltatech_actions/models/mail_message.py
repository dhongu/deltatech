# ©  2024 Terrabit
#              Dan Stoica <danila(@)terrabit(.)ro
# See README.rst file on addons root folder for license details

import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, models
from odoo.tools import SQL, str2bool

from .cleanup_summary import check_cleanup_access, log_prefix

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
        check_cleanup_access(self.env)
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
        # ACTIONS-002: without exclusions there is no array to bind to LIKE ANY(...),
        # so the predicate is left out instead of comparing against False. Messages
        # without a model stay out either way, as they always did with exclusions.
        exclude_clause = SQL("AND NOT (model LIKE ANY(%s))", list(exclude_models)) if exclude_models else SQL()
        pattern_clause = SQL("AND subject LIKE %s", pattern) if pattern else SQL()
        query = SQL(
            """SELECT id FROM mail_message
            WHERE model IS NOT NULL AND create_date <= %s
            %s
            %s
            ORDER BY id
            LIMIT %s;
            """,
            max_date,
            exclude_clause,
            pattern_clause,
            limit,
        )
        self.env.cr.execute(query)
        res = self.env.cr.fetchall()
        message_ids = [item[0] for item in res]
        messages_to_delete = self.browse(message_ids)
        all_attachments = messages_to_delete.attachment_ids
        attachments_to_delete = self.env["ir.attachment"]
        # avoid deleting anaf attachments
        for attachment in all_attachments:
            if attachment.mimetype not in ["application/xml", "application/zip", "text/plain"]:
                attachments_to_delete |= attachment
        # counted before the unlink: the recordsets are unusable afterwards
        message_count = len(messages_to_delete)
        attachment_count = len(attachments_to_delete)
        attachment_size = sum(attachments_to_delete.mapped("file_size"))
        if not dry_run:
            # ACTIONS-005: a refused deletion is raised, not logged and reported as done
            attachments_to_delete.sudo().unlink()
            messages_to_delete.sudo().unlink()
        _logger.info(f"{log_prefix(dry_run)} {message_count} messages and {attachment_count} linked attachments.")
        return {
            "count": message_count,
            "size": attachment_size,
            "attachments": attachment_count,
            "dry_run": dry_run,
        }
