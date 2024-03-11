# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, body="", **kwargs):
        if not body:
            return super().message_post(body=body, **kwargs)
        body_subs = self.env["mail.body.substitution"].search([])
        for sub in body_subs:
            body = body.replace(sub.body_part, sub.substitution)
        return super().message_post(body=body, **kwargs)
