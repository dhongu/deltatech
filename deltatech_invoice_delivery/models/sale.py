# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    from_invoice_id = fields.Many2one("account.move", string="Generated from the invoice", copy=False)

    def _check_invoice_delivery_steps(self):
        for order in self:
            if order.warehouse_id.delivery_steps != "ship_only":
                raise UserError(
                    self.env._(
                        "Delivery from invoice works only with warehouses that deliver in one step. "
                        "Warehouse %s uses more steps.",
                        order.warehouse_id.display_name,
                    )
                )

    def _check_invoice_delivery_availability(self, picking):
        """Raise an explicit error for the products that cannot be delivered"""
        errors = []
        for move in picking.move_ids.filtered(lambda m: m.product_uom_qty > 0):
            if move.product_uom.compare(move.quantity, move.product_uom_qty) < 0:
                errors.append(
                    self.env._(
                        "%(product)s: available %(available)s %(uom)s, requested %(requested)s %(uom)s",
                        product=move.product_id.display_name,
                        available=move.quantity,
                        requested=move.product_uom_qty,
                        uom=move.product_uom.name,
                    )
                )
            elif move.has_tracking != "none" and any(not ml.lot_id for ml in move.move_line_ids):
                errors.append(
                    self.env._(
                        "%(product)s: the lot or serial number could not be reserved",
                        product=move.product_id.display_name,
                    )
                )
        if errors:
            raise UserError(self.env._("The invoice cannot be posted, the stock is not enough:\n%s", "\n".join(errors)))

    def delivery_from_stock(self, delivery_date=None):
        """Validate the deliveries of the order with the demanded quantities"""
        for order in self:
            date = delivery_date or order.date_order
            for picking in order.picking_ids.filtered(lambda p: p.state not in ("done", "cancel")):
                picking.action_assign()
                if picking.picking_type_id.code == "outgoing":
                    order._check_invoice_delivery_availability(picking)
                for move in picking.move_ids.filtered(lambda m: m.product_uom_qty > 0):
                    if move.product_uom.compare(move.quantity, move.product_uom_qty) != 0:
                        move.quantity = move.product_uom_qty
                    move.picked = True
                if "to_invoice" in picking._fields:
                    picking.to_invoice = False
                picking.with_context(force_period_date=date)._action_done()
