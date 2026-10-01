# ©  2008-2022 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    alternative_code = fields.Char(string="Alternative Code", related="product_id.alternative_code", store=False)
