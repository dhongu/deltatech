# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    def _action_send_mail_comment(self, res_ids):
        messages = super()._action_send_mail_comment(res_ids)
        if self.model == "purchase.send.xlsx.wizard":
            wizards = self.env[self.model].browse(res_ids)
            for wizard in wizards:
                for message in messages.filtered(lambda msg, wizard=wizard: msg.res_id == wizard.id):
                    wizard.purchase_ids._log_sent_email(message)
        return messages
