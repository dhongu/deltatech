# ©  2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, models
from odoo.tools import float_compare


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        self.prepare_transfer()
        return res

    def prepare_transfer(self):
        precision = self.env["decimal.precision"].precision_get("Product Unit of Measure")

        for order in self:
            domain = [("id", "!=", order.warehouse_id.id), ("company_id", "=", order.company_id.id)]
            warehouse = self.env["stock.warehouse"].search(domain, limit=1)
            if not warehouse:
                continue

            pick_type = warehouse.pick_type_auto_transfer_id or warehouse.int_type_id

            location_source = warehouse.int_type_id.default_location_src_id
            location_dest = order.warehouse_id.int_type_id.default_location_dest_id
            if order.warehouse_id.group_transfer_with_delivery:
                group_id = order.procurement_group_id.id
            else:
                group_id = False

            picking = self.env["stock.picking"]
            for line in order.order_line:
                if line.product_id.type != "product":
                    continue

                product = line.product_id.with_context(warehouse=order.warehouse_id.id)
                product_qty = line.product_uom._compute_quantity(line.product_uom_qty, line.product_id.uom_id)

                if float_compare(product.virtual_available, product_qty, precision_digits=precision) == -1:
                    demand = line.product_uom_qty - product.qty_available
                    if demand <= 0:
                        continue
                    qty_available = line.product_id.with_context(warehouse=warehouse.id).qty_available
                    if qty_available > 0:
                        if not picking:
                            picking = self.env["stock.picking"].create(
                                {
                                    "partner_id": order.partner_id.id,
                                    "location_id": location_source.id,
                                    "location_dest_id": location_dest.id,
                                    "picking_type_id": pick_type.id,
                                    "origin": order.name,
                                }
                            )

                        if demand < qty_available:
                            qty = demand
                        else:
                            qty = qty_available

                        self.env["stock.move"].create(
                            {
                                "state": "confirmed",
                                "product_id": line.product_id.id,
                                "picking_id": picking.id,
                                "product_uom": line.product_uom.id,
                                "product_uom_qty": qty,
                                "name": product.name,
                                "location_id": location_source.id,
                                "location_dest_id": location_dest.id,
                                "group_id": group_id,
                            }
                        )

            if picking:
                picking.message_post_with_view(
                    "mail.message_origin_link",
                    values={"self": picking, "origin": order},
                    subtype_id=self.env.ref("mail.mt_note").id,
                )
                picking.action_assign()
                link = (
                    "<a href=# data-oe-model=stock.picking data-oe-id=" + str(picking.id) + ">" + picking.name + "</a>"
                )
                message = _("Transfer document %s was generated") % link
                order.message_post(body=message)

                # order.picking_ids.message_post(body=message)
                if "confirm_transfer" in self.env.context:
                    picking.auto_transfer()
