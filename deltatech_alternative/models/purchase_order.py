# ©  2008-2023 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    alternative_code = fields.Char(string="Alternative Code", related="product_id.alternative_code", store=False)
