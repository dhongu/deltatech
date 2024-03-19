# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    product_category_id = fields.Many2one(
        "product.category", string="Product category", related="product_id.categ_id", store=True
    )
