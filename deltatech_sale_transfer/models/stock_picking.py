# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def auto_transfer(self):
        for picking in self:
            picking.action_assign()  # verifica disponibilitate
            if not all(move.state == "assigned" for move in picking.move_ids):
                raise UserError(self.env._("Not all products are available."))

            for move in picking.move_ids:
                if move.product_uom_qty > 0:
                    # rezervarea completa a mișcării a stabilit deja cantitatea pe liniile de mișcare;
                    # daca nu exista linii de mișcare se scrie cantitatea direct pe mișcare
                    if not move.move_line_ids:
                        move.write({"quantity": move.product_uom_qty})
                    move.picked = True
                else:
                    move.unlink()
            picking._action_done()
            message = self.env._("Automatically validated transfer upon order confirmation")
            picking.message_post(body=message)
