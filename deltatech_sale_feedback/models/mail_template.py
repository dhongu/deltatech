# ©  2015-2022 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import logging

from odoo import models

_logger = logging.getLogger(__name__)


class MailTemplate(models.Model):
    _inherit = "mail.template"

    def send_mail(self, res_id, force_send=False, raise_exception=False, email_values=None, notif_layout=False):
        record = self.env[self.model].browse(res_id)
        template = self
        if "company_id" in record and record["company_id"]:
            web_base_url = record.company_id.website
            if web_base_url:
                template = self.with_context(web_base_url=web_base_url)
        return super(MailTemplate, template).send_mail(res_id, force_send, raise_exception, email_values, notif_layout)
