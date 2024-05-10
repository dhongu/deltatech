# ©  2024 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    def _default_sale_followup_template_id(self):
        try:
            return self.env.ref("deltatech_sale_followup.mail_template_sale_followup").id
        except ValueError:
            return False

    sale_followup = fields.Boolean("Email followup after sale", default=False)
    sale_followup_template_id = fields.Many2one(
        "mail.template",
        string="Email Template Followup",
        domain="[('model', '=', 'sale.order')]",
        default=_default_sale_followup_template_id,
        help="Email sent to the customer after delivery sale order .",
    )
