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
                    picking.with_context(force_period_date=order.date_order).action_done()


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
        Launch procurement group run method with required/custom fields genrated by a
        sale order line. procurement group will launch '_run_pull', '_run_buy' or '_run_manufacture'
        depending on the sale order line product rule.
        """
        super(SaleOrderLine, self)._action_launch_stock_rule(previous_product_uom_qty)
        precision = self.env["decimal.precision"].precision_get("Product Unit of Measure")
        procurements = []
        for line in self:
            if line.state != "sale" or line.product_id.type not in ("consu", "product"):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty, precision_digits=precision) < 0:
                continue

            group_id = line._get_procurement_group()
            if not group_id:
                group_id = self.env["procurement.group"].create(line._prepare_procurement_group_vals())
                line.order_id.procurement_group_id = group_id
            else:
                # In case the procurement group is already created and the order was
                # cancelled, we need to update certain values of the group.
                updated_vals = {}
                if group_id.partner_id != line.order_id.partner_shipping_id:
                    updated_vals.update({"partner_id": line.order_id.partner_shipping_id.id})
                if group_id.move_type != line.order_id.picking_policy:
                    updated_vals.update({"move_type": line.order_id.picking_policy})
                if updated_vals:
                    group_id.write(updated_vals)

            values = line._prepare_procurement_values(group_id=group_id)
            product_qty = line.product_uom_qty - qty

            line_uom = line.product_uom
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(product_qty, quant_uom)
            procurements.append(
                self.env["procurement.group"].Procurement(
                    line.product_id,
                    product_qty,
                    procurement_uom,
                    line.order_id.partner_shipping_id.property_stock_customer,
                    line.name,
                    line.order_id.name,
                    line.order_id.company_id,
                    values,
                )
            )
        if procurements:
            self.env["procurement.group"].run(procurements)

        pickings = self.env["stock.picking"]
        for move in self.move_ids:

            if move.product_uom_qty < 0:
                move.write(
                    {
                        "product_uom_qty": -move.product_uom_qty,
                        "location_id": move.location_dest_id.id,
                        "location_dest_id": move.location_id.id,
                        "state": "assigned",
                        "to_refund": True,
                    }
                )
                pickings |= move.picking_id

        for picking in pickings:
            picking.write({"state": "draft"})
            picking.write(
                {
                    "picking_type_id": picking.picking_type_id.return_picking_type_id.id or picking.picking_type_id.id,
                    "location_id": picking.location_dest_id.id,
                    "location_dest_id": picking.location_id.id,
                    "state": "assigned",
                }
            )

        return True
