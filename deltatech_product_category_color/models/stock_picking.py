# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    categ_ids = fields.Many2many("product.category", compute="_compute_categ_ids")

    @api.depends("move_ids.product_id.categ_id", "move_ids.state")
    def _compute_categ_ids(self):
        # from the moves, not from the move lines: unreserved transfers have no move lines
        for picking in self:
            moves = picking.move_ids.filtered(lambda move: move.state != "cancel")
            picking.categ_ids = moves.product_id.categ_id
