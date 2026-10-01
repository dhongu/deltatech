# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo import models, tools

_logger = logging.getLogger(__name__)


class MailMail(models.Model):
    _inherit = "mail.mail"

    def _get_mail_substitutions(self):
        """Substitutions that apply to this email: the ones bound to its model
        and the generic ones (no model)."""
        self.ensure_one()
        substitutions = self.env["mail.substitution"].sudo().search([("email", "!=", False)])
        message_id = self.message_id or ""
        return substitutions.filtered(
            lambda s: not s.name or s.name == self.model or (not self.model and s.name in message_id)
        )

    def _get_substituted_email_from(self):
        """Sender to use when sending: the author's company email when
        ``mail.use_company_email`` is set, then a "sender" substitution."""
        self.ensure_one()
        email_from = self.email_from
        if self.env["ir.config_parameter"].sudo().get_bool("mail.use_company_email"):
            author = self.author_id
            company = author.company_id or author.user_ids[:1].company_id or self.env.company
            if company.email:
                email_from = tools.formataddr((company.name, company.email))
            else:
                _logger.warning("Mail %s: company %s has no email, sender left unchanged", self.id, company.name)
        senders = self._get_mail_substitutions().filtered(lambda s: s.type == "sender")
        if senders:
            email_from = senders[0].email
        return email_from

    def send(self, auto_commit=False, raise_exception=False, post_send_callback=None):
        # the sender is read from the record before the outgoing values are
        # prepared, and it also selects the mail server: set it before sending
        for mail in self.filtered(lambda m: m.state == "outgoing"):
            email_from = mail._get_substituted_email_from()
            if email_from and email_from != mail.email_from:
                mail.email_from = email_from
        return super().send(
            auto_commit=auto_commit, raise_exception=raise_exception, post_send_callback=post_send_callback
        )

    def _prepare_outgoing_list(self, mail_server=False, doc_to_followers=None):
        res = super()._prepare_outgoing_list(mail_server=mail_server, doc_to_followers=doc_to_followers)
        receivers = self._get_mail_substitutions().filtered(lambda s: s.type == "receiver")
        if not receivers:
            return res
        email_to = receivers.mapped("email")
        email_to_normalized = tools.mail.email_normalize_all(",".join(email_to))
        # redirect every outgoing email (one per recipient partner, so the
        # personalized body and the notification status are kept) and drop
        # the copies, otherwise the original recipients would still be reached
        for email in res:
            email.update(
                {
                    "email_to": email_to,
                    "email_cc": [],
                    "email_to_normalized": email_to_normalized,
                }
            )
        return res
