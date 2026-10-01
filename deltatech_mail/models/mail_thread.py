# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import logging

from markupsafe import Markup

from odoo import models, tools
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def message_post(self, body="", **kwargs):
        if not body:
            return super().message_post(body=body, **kwargs)
        body_subs = self.env["mail.body.substitution"].search([])
        for sub in body_subs:
            if isinstance(body, str):
                body = str(body).replace(str(sub.body_part), str(sub.substitution))
                body = Markup(body)
        return super().message_post(body=body, **kwargs)

    def _message_compute_author(self, author_id=None, email_from=None):
        computed_from = email_from is None
        author_id, email_from = super()._message_compute_author(author_id=author_id, email_from=email_from)
        # only the sender Odoo derives from the author is replaced, an explicit
        # email_from (incoming email, template) is kept
        use_company_email = self.env["ir.config_parameter"].sudo().get_param("mail.use_company_email", "False")
        if computed_from and tools.str2bool(use_company_email, False):
            company = self.env.user.company_id
            if not company.email:
                raise UserError(self.env._("Unable to post message, please configure the company's email address."))
            email_from = tools.formataddr((company.name, company.email))
        return author_id, email_from
