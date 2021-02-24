# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_ready = fields.Boolean(string="Is ready", compute="_compute_is_ready")

    # aceasta functie poate sa fie consumatoare de resurse !
    # trebuie sa scaneze stocurile pentru toate produsele din comenzile de vanzare afisate

    def _compute_is_ready(self):
        for order in self:
            is_ready = order.state in ["draft", "sent", "sale", "done"] and order.invoice_status != "invoiced"
            if is_ready:
                if order.picking_policy == "direct":
                    is_ready = False
                    for line in order.order_line:
                        is_ready = is_ready or (line.product_id.qty_available >= line.qty_to_deliver)
                else:
                    for line in order.order_line:
                        is_ready = is_ready and (line.product_id.qty_available >= line.qty_to_deliver)

            if is_ready:
                # verific daca comanzile de livrare au stocul rezervat
                if order.picking_policy == "direct":
                    is_ready = False
                    for picking in order.picking_ids:
                        for move in picking.move_lines:
                            is_ready = is_ready or move.reserved_availability > 0
                else:
                    for picking in order.picking_ids:
                        for move in picking.move_lines:
                            is_ready = is_ready and (move.reserved_availability == move.product_uom_qty)

            order.is_ready = is_ready
