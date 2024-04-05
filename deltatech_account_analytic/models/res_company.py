# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    can_split_analytic = fields.Boolean(compute="_compute_can_split")
    split_sale_analytic = fields.Boolean(
        string="Split sale analytic", help="Split sale analytic in stock value and margin"
    )

    def _compute_can_split(self):
        domain = [("name", "=", "deltatech_sale_commission"), ("state", "=", "installed")]
        sale_commission = self.env["ir.module.module"].sudo().search(domain)
        for company in self:
            if sale_commission:
                company.can_split_analytic = True
            else:
                company.can_split_analytic = False
