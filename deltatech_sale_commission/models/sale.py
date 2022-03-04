# ©  2017-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    commission = fields.Float(string="Commission", default=0.0)
