# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MRPSimple(models.TransientModel):
    _name = "mrp.simple"
    _description = "MRP Simple"

    product_in_ids = fields.One2many("mrp.simple.line.in", "mrp_simple_id")
    product_out_ids = fields.One2many("mrp.simple.line.out", "mrp_simple_id")

    picking_type_consume = fields.Many2one(
        "stock.picking.type",
        string="Picking type consume",
        required=True,
    )
    picking_type_receipt_production = fields.Many2one(
        "stock.picking.type", string="Picking type receipt", required=True
    )

    date = fields.Date(string="Date", default=fields.Date.today, required=True)

    validation_consume = fields.Boolean()
    validation_receipt = fields.Boolean(default=True)

    sale_order_id = fields.Many2one("sale.order", string="Sale Order")

    def do_transfer(self):

        picking_type_consume = self.picking_type_consume
        picking_type_receipt_production = self.picking_type_receipt_production

        context = {"default_picking_type_id": picking_type_receipt_production.id}
        picking_in = (
            self.env["stock.picking"]
            .with_context(context)
            .create({"picking_type_id": picking_type_receipt_production.id, "date": self.date})
        )

        context = {"default_picking_type_id": picking_type_consume.id}
        picking_out = (
            self.env["stock.picking"]
            .with_context(context)
            .create({"picking_type_id": picking_type_consume.id, "date": self.date})
        )

        for line in self.product_in_ids:
            if line.price_unit:
                self.add_picking_line(
                    picking=picking_in,
                    product=line.product_id,
                    quantity=line.quantity,
                    uom=line.uom_id,
                    price_unit=line.price_unit,
                )
            else:
                raise UserError(_("Price 0 for result product!"))

        for line in self.product_out_ids:
            self.add_picking_line(
                picking=picking_out,
                product=line.product_id,
                quantity=line.quantity,
                uom=line.uom_id,
                price_unit=line.product_id.standard_price,
            )

        # adaugare picking ids in sale order
        if self.sale_order_id:
            self.sale_order_id.update({"simple_mrp_picking_ids": [(4, picking_in.id, False)]})
            self.sale_order_id.update({"simple_mrp_picking_ids": [(4, picking_out.id, False)]})

        # se face consumul
        if picking_out.move_lines:
            picking_out.action_assign()
            if self.validation_consume:
                if picking_out.state == "assigned":
                    for move in picking_out.move_lines:
                        for move_line in move.move_line_ids:
                            move_line.qty_done = move_line.product_uom_qty
                picking_out.button_validate()

        # se face receptia
        if picking_in.move_lines:
            picking_in.action_assign()
            if self.validation_receipt:
                if picking_in.state == "assigned":
                    for move in picking_in.move_lines:
                        for move_line in move.move_line_ids:
                            move_line.qty_done = move_line.product_uom_qty
                picking_in.button_validate()

        return {
            "domain": [("id", "in", [picking_in.id, picking_out.id])],
            "name": _("Consumption & Receipt"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "stock.picking",
            "view_id": False,
            "context": {},
            "type": "ir.actions.act_window",
        }

    def add_picking_line(self, picking, product, quantity, uom, price_unit):
        move = self.env["stock.move"].search(
            [("picking_id", "=", picking.id), ("product_id", "=", product.id), ("product_uom", "=", uom.id)]
        )
        if move:
            qty = move.product_uom_qty + quantity
            move.write({"product_uom_qty": qty})
        else:
            values = {
                "state": "confirmed",
                "product_id": product.id,
                "product_uom": uom.id,
                "product_uom_qty": quantity,
                # 'quantity_done': quantity,  # o fi bine >???
                "name": product.name,
                "picking_id": picking.id,
                "price_unit": price_unit,
                "location_id": picking.picking_type_id.default_location_src_id.id,
                "location_dest_id": picking.picking_type_id.default_location_dest_id.id,
                "picking_type_id": picking.picking_type_id.id,
            }

            move = self.env["stock.move"].create(values)
        return move


class MRPSimpleLineIn(models.TransientModel):
    _name = "mrp.simple.line.in"
    _description = "MRP Simple Line IN"

    mrp_simple_id = fields.Many2one("mrp.simple")
    product_id = fields.Many2one("product.product")
    quantity = fields.Float(string="Quantity", digits="Product Unit of Measure", default=1)
    price_unit = fields.Float("Unit Price", digits="Product Price")
    uom_id = fields.Many2one("uom.uom", "Unit of Measure")

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.uom_id = self.product_id.uom_id

    @api.onchange("quantity")
    def compute_finit_price(self):
        mrpsimple = self.mrp_simple_id
        price = 0.0
        for line in mrpsimple.product_out_ids:
            price += line.product_id.standard_price * line.quantity
        for line in mrpsimple.product_in_ids:
            line.price_unit = price / line.quantity


class MRPSimpleLineOut(models.TransientModel):
    _name = "mrp.simple.line.out"
    _description = "MRP Simple Line OUT"

    mrp_simple_id = fields.Many2one("mrp.simple")
    product_id = fields.Many2one("product.product")
    quantity = fields.Float(string="Quantity", digits="Product Unit of Measure", default=1)
    price_unit = fields.Float("Unit Price", digits="Product Price")
    uom_id = fields.Many2one("uom.uom", "Unit of Measure")

    @api.onchange("product_id", "quantity")
    def onchange_product_id(self):
        self.uom_id = self.product_id.uom_id
        self.price_unit = self.product_id.standard_price
