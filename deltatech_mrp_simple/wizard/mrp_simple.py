# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

import odoo.addons.decimal_precision as dp


class MRPSimple(models.TransientModel):
    _name = "mrp.simple"

    product_in_ids = fields.One2many(
        "mrp.simple.line", "mrp_simple_id", domain=[("type", "=", "receipt")], context={"default_type": "receipt"}
    )
    product_out_ids = fields.One2many(
        "mrp.simple.line",
        "mrp_simple_id",
        domain=[("type", "=", "consumption")],
        context={"default_type": "consumption"},
    )

    picking_type_consume = fields.Many2one("stock.picking.type", string="Picking type consume", required=True,)
    picking_type_receipt_production = fields.Many2one(
        "stock.picking.type", string="Picking type receipt", required=True
    )

    date = fields.Date(string="Date", default=fields.Date.today, required=True)

    validation_consume = fields.Boolean()
    validation_receipt = fields.Boolean(default=True)

    picking_in = fields.Many2one("stock.picking")
    picking_out = fields.Many2one("stock.picking")

    price_in = fields.Float("Component price", compute="_compute_component_price")

    @api.multi
    @api.depends("product_out_ids")
    def _compute_component_price(self):
        sum = 0.0
        for line in self.product_out_ids:
            sum += line.product_id.standard_price * line.quantity
        self.price_in = sum

    @api.multi
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

        self.write({"picking_in": picking_in.id, "picking_out": picking_out.id})

        for line in self.product_in_ids:
            line.product_id.write(
                {"standard_price": line.price_unit,}
            )
            self.add_picking_line(picking=picking_in, line=line, price_unit=line.price_unit)

        for line in self.product_out_ids:
            self.add_picking_line(picking=picking_out, line=line, price_unit=line.product_id.standard_price)

        self.do_consumption(picking_out)
        self.do_reception(picking_in)

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

    def do_consumption(self, picking_out):
        # se face consumul
        if picking_out.move_lines:
            picking_out.action_assign()
            if self.validation_consume:
                if picking_out.state == "assigned":
                    for move in picking_out.move_lines:
                        for move_line in move.move_line_ids:
                            move_line.qty_done = move_line.product_uom_qty
                picking_out.button_validate()

    def do_reception(self, picking_in):
        # se face receptia
        if picking_in.move_lines:
            picking_in.action_assign()
            if self.validation_receipt:
                if picking_in.state == "assigned":
                    for move in picking_in.move_lines:
                        for move_line in move.move_line_ids:
                            move_line.qty_done = move_line.product_uom_qty
                picking_in.button_validate()

    def add_picking_line(self, picking, line=None, price_unit=None, product=None, quantity=None, uom=None):
        product = line.product_id
        quantity = line.quantity
        uom = line.uom_id
        return self.add_picking_line_detail(picking, product, quantity, uom, price_unit)

    def add_picking_line_detail(self, picking, product, quantity, uom, price_unit=None):

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
                "location_id": picking.picking_type_id.default_location_src_id.id,
                "location_dest_id": picking.picking_type_id.default_location_dest_id.id,
                "picking_type_id": picking.picking_type_id.id,
            }
            if price_unit:
                values["price_unit"] = price_unit

            move = self.env["stock.move"].create(values)
        return move


class MRPSimpleLine(models.TransientModel):
    _name = "mrp.simple.line"

    mrp_simple_id = fields.Many2one("mrp.simple")
    product_id = fields.Many2one("product.product")
    quantity = fields.Float(string="Quantity", digits=dp.get_precision("Product Unit of Measure"), default=1)
    price_unit = fields.Float("Unit Price", digits=dp.get_precision("Product Price"))
    uom_id = fields.Many2one("product.uom", "Unit of Measure")
    type = fields.Selection(
        [("consumption", "Consumption in production"), ("receipt", "Receipt from production")], string="Type"
    )

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.uom_id = self.product_id.uom_id
