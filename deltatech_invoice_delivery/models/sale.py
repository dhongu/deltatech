# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    from_invoice_id = fields.Many2one("account.move", string="Generated from the invoice")

    def delivery_from_stock(self):
        """
        Matoda aceasta este utilizata si in fast purchase
        """
        for order in self:
            for picking in order.picking_ids:
                if picking.state not in ["done", "cancel"]:
                    picking.action_assign()  # verifica disponibilitate
                    if not all(move.state == "assigned" for move in picking.move_lines):
                        raise UserError(_("Not all products are available."))

                    for move_line in picking.move_lines:
                        if move_line.product_uom_qty > 0 and move_line.quantity_done == 0:
                            move_line.write({"quantity_done": move_line.product_uom_qty})
                        else:
                            move_line.unlink()
                    picking.with_context(force_period_date=order.date_order)._action_done()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):

        super(SaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)
        precision = self.env["decimal.precision"].precision_get("Product Unit of Measure")

        for line in self:
            if line.state != "sale" or line.product_id.type not in ("consu", "product"):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) < 0:
                continue
            if line.product_uom_qty >= 0:
                continue

            group_id = line.order_id.procurement_group_id
            if not group_id:
                group_id = self.env["procurement.group"].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(-product_qty, quant_uom)
            location_id = line.order_id.partner_shipping_id.property_stock_customer
            rule = group_id._get_rule(line.product_id, location_id, values)

            picking = self.env["stock.picking"].create(
                {
                    "picking_type_id": rule.picking_type_id.return_picking_type_id.id or rule.picking_type_id.id,
                    # "picking_type_id": rule.picking_type_id.id,
                    "partner_id": line.order_id.partner_shipping_id.id,
                    "origin": line.order_id.name,
                    "group_id": group_id.id,
                    "location_id": rule.location_id.id,
                    "location_dest_id": rule.location_src_id.id,
                    "sale_id": line.order_id.id,
                    "state": "draft",
                    "move_type": "one",
                }
            )
            self.env["stock.move"].create(
                {
                    "picking_id": picking.id,
                    "location_id": rule.location_id.id,
                    "location_dest_id": rule.location_src_id.id,
                    "product_id": line.product_id.id,
                    "name": line.product_id.name,
                    "product_uom_qty": product_qty,
                    "product_uom": procurement_uom.id,
                    "state": "draft",
                    "to_refund": True,
                    "sale_line_id": line.id,
                }
            )
            picking.write(
                {
                    "group_id": group_id.id,
                    "sale_id": line.order_id.id,
                }
            )

            picking.action_assign()

        return True
