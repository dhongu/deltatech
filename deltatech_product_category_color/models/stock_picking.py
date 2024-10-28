# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    categ_ids = fields.Many2many("product.category", compute="_compute_categ_ids")

    def _compute_categ_ids(self):
        for picking in self:
            categ_ids = picking.move_line_ids.mapped("product_id.categ_id")
            picking.categ_ids = categ_ids
