# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    is_ready = fields.Boolean(string="Is ready", compute="_compute_is_ready", store=False, search="_search_is_ready")

    # @api.depends('state', 'invoice_status', 'order_line.product_id.qty_available', 'order_line.qty_to_deliver',
    #              'picking_ids.move_ids.reserved_availability')
    def _compute_is_ready(self):
        for order in self:
            is_ready = order.state in ["draft", "sent", "sale"] and order.invoice_status not in ["invoiced"]
            if is_ready and order.state == "draft":
                if order.picking_policy == "direct":
                    is_ready = False
                    for line in order.order_line:
                        available = line.product_id.qty_available - line.product_id.outgoing_qty
                        is_ready = is_ready or (available >= line.qty_to_deliver)
                else:
                    for line in order.order_line:
                        available = line.product_id.qty_available - line.product_id.outgoing_qty
                        is_ready = is_ready and (available >= line.qty_to_deliver)

            if is_ready and order.state != "draft":
                # verific daca comanzile de livrare au stocul rezervat
                if order.picking_policy == "direct":
                    is_ready = False
                    for picking in order.picking_ids:
                        for move in picking.move_ids:
                            is_ready = is_ready or move.reserved_availability > 0
                else:
                    for picking in order.picking_ids:
                        if picking.state in ["done"]:
                            continue
                        for move in picking.move_ids:
                            is_ready = is_ready and (move.reserved_availability == move.product_uom_qty)
            order.is_ready = is_ready

    @api.model
    def _search_is_ready(self, operator, value):
        # comenzi deschise
        orders = self.env["sale.order"].search(
            [("state", "in", ["draft", "sent", "sale"]), ("invoice_status", "!=", "invoiced")]
        )
        ready_orders = self.env["sale.order"]
        for order in orders:
            if order.is_ready:
                ready_orders += order
        if operator == "=" and value:
            domain = [("id", "in", ready_orders.ids)]
        else:
            domain = [("id", "not in", ready_orders.ids)]
        return domain
