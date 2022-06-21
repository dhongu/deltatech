# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    def _default_sale_feedback_template_id(self):
        try:
            return self.env.ref("deltatech_sale_feedback.mail_template_sale_feedback").id
        except ValueError:
            return False

    sale_feedback = fields.Boolean("Email feedback after sale", default=False)
    sale_feedback_template_id = fields.Many2one(
        "mail.template",
        string="Email Template AWB picked",
        domain="[('model', '=', 'account.move')]",
        default=_default_sale_feedback_template_id,
        help="Email sent to the customer after invoice for feedback.",
    )
