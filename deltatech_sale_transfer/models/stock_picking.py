# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def auto_transfer(self):
        for picking in self:
            picking.action_assign()  # verifica disponibilitate
            if not all(move.state == "assigned" for move in picking.move_lines):
                raise UserError(_("Not all products are available."))

            for move in picking.move_lines:
                if move.product_uom_qty > 0 and move.quantity_done == 0:
                    # check if move has multiple move lines. You cannot set quantity_done if so
                    move_line_ids = move._get_move_lines()
                    if len(move_line_ids) > 1:
                        for stock_move_line in move_line_ids:
                            stock_move_line.write({"qty_done": stock_move_line.product_uom_qty})
                    else:
                        move.write({"quantity_done": move.product_uom_qty})
                else:
                    move.unlink()
            picking.action_done()
            message = _("Automatically validated transfer upon order confirmation")
            picking.message_post(body=message)
