# ©  2023-now Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = "account.analytic.line"

    product_category_id = fields.Many2one(
        "product.category", string="Product category", related="product_id.categ_id", store=True
    )
    team_id = fields.Many2one("crm.team")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "move_line_id" in vals and vals["move_line_id"]:
                move_line_id = self.env["account.move.line"].browse(vals["move_line_id"])
                stock_move_id = move_line_id.move_id.stock_move_ids[:1]
                if move_line_id.move_id.move_type == "entry" and stock_move_id:
                    picking_id = stock_move_id.picking_id
                    if picking_id and picking_id.sale_id:
                        vals["team_id"] = picking_id.sale_id.team_id.id
                elif move_line_id.move_id.move_type in ["out_invoice", "out_refund", "out_receipt"]:
                    vals["team_id"] = move_line_id.move_id.team_id.id
        return super().create(vals_list)
