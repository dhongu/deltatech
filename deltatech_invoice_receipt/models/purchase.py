# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_compare
from odoo.tools.translate import _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    notice = fields.Boolean()


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    from_invoice_id = fields.Many2one("account.move", string="Generated from the invoice")

    def receipt_to_stock(self):
        """
        Matoda aceasta este utilizata si in fast purchase
        """
        for purchase_order in self:
            for picking in purchase_order.picking_ids:
                if picking.state == "confirmed":
                    picking.action_assign()
                    if picking.state != "assigned":
                        raise UserError(_("The stock transfer cannot be validated!"))
                if picking.state == "assigned":
                    picking.write({"notice": False, "origin": purchase_order.partner_ref})
                    for move_line in picking.move_lines:
                        if move_line.product_uom_qty > 0 and move_line.quantity_done == 0:
                            move_line.write({"quantity_done": move_line.product_uom_qty})
                        else:
                            move_line.unlink()
                    # pentru a se prelua data din comanda de achizitie
                    picking.with_context(force_period_date=purchase_order.date_order)._action_done()

    def _create_picking(self):
        StockPicking = self.env["stock.picking"]
        super(PurchaseOrder, self)._create_picking()
        for order in self:
            if any(
                [line.product_id.type in ["product", "consu"] and line.product_qty < 0 for line in order.order_line]
            ):
                res = order._prepare_picking()
                res.update(
                    {
                        "picking_type_id": self.picking_type_id.return_picking_type_id.id or self.picking_type_id.id,
                        "location_id": self._get_destination_location(),
                        "location_dest_id": self.partner_id.property_stock_supplier.id,
                    }
                )
                picking = StockPicking.create(res)

                moves = order.order_line.with_context(return_picking=True)._create_stock_moves(picking)
                moves = moves.filtered(lambda x: x.state not in ("done", "cancel"))._action_confirm()

                moves._action_assign()
                picking.message_post_with_view(
                    "mail.message_origin_link",
                    values={"self": picking, "origin": order},
                    subtype_id=self.env.ref("mail.mt_note").id,
                )


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def _prepare_stock_moves(self, picking):
        if self.product_qty > 0:
            return super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        if not self.env.context.get("return_picking", False):
            return []

        self.ensure_one()
        res = []
        if self.product_id.type not in ["product", "consu"]:
            return res
        qty = 0.0
        price_unit = self._get_stock_move_price_unit()
        outgoing_moves, incoming_moves = self._get_outgoing_incoming_moves()
        for move in outgoing_moves:
            qty -= move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method="HALF-UP")
        for move in incoming_moves:
            qty += move.product_uom._compute_quantity(move.product_uom_qty, self.product_uom, rounding_method="HALF-UP")
        description_picking = self.product_id.with_context(
            lang=self.order_id.dest_address_id.lang or self.env.user.lang
        )._get_description(self.order_id.picking_type_id)
        template = {
            # truncate to 2000 to avoid triggering index limit error
            # TODO: remove index in master?
            "name": (self.name or "")[:2000],
            "product_id": self.product_id.id,
            "product_uom": self.product_uom.id,
            "date": self.order_id.date_order,
            "location_dest_id": self.order_id.partner_id.property_stock_supplier.id,
            "location_id": self.order_id._get_destination_location(),
            "picking_id": picking.id,
            "partner_id": self.order_id.dest_address_id.id,
            "move_dest_ids": [(4, x) for x in self.move_dest_ids.ids],
            "state": "draft",
            "purchase_line_id": self.id,
            "company_id": self.order_id.company_id.id,
            "price_unit": price_unit,
            "picking_type_id": self.order_id.picking_type_id.return_picking_type_id.id,
            "group_id": self.order_id.group_id.id,
            "origin": self.order_id.name,
            "to_refund": True,
            "description_picking": description_picking,
            "propagate_cancel": self.propagate_cancel,
            "route_ids": self.order_id.picking_type_id.warehouse_id
            and [(6, 0, [x.id for x in self.order_id.picking_type_id.warehouse_id.route_ids])]
            or [],
            "warehouse_id": self.order_id.picking_type_id.warehouse_id.id,
        }
        diff_quantity = self.product_qty + qty
        if float_compare(diff_quantity, 0.0, precision_rounding=self.product_uom.rounding) < 0:
            po_line_uom = self.product_uom
            quant_uom = self.product_id.uom_id
            product_uom_qty, product_uom = po_line_uom._adjust_uom_quantities(-diff_quantity, quant_uom)
            template["product_uom_qty"] = product_uom_qty
            template["product_uom"] = product_uom.id
            res.append(template)
        return res
