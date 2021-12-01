# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    sale_simple_mrp_id = fields.Many2one("sale.order", string="Sales Order", store=True, readonly=False)
