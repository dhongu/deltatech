# © Terrabit
# See LICENSE file for full copyright and licensing details.


from odoo import fields, models


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    batch_picking_id = fields.Many2one("stock.picking.batch")
