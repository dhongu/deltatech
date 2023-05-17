# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models
from odoo.exceptions import ValidationError


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def message_subscribe(self, partner_ids=None, channel_ids=None, subtype_ids=None):
        try:
            return super().message_subscribe(partner_ids=partner_ids, channel_ids=channel_ids, subtype_ids=subtype_ids)
        except ValidationError:
            return True
