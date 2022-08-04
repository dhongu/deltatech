# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MRPSimple(models.Model):
    _name = "mrp.simple"
    _description = "MRP Simple"

    name = fields.Char()
    consume_id = fields.Many2one("stock.picking", string="Consume", copy=False)
    receipt_id = fields.Many2one("stock.picking", string="Receipt", copy=False)
    state = fields.Selection([("draft", "Draft"), ("done", "Done")], default="draft")
    product_in_ids = fields.One2many("mrp.simple.line.in", "mrp_simple_id", string="Received products", copy=True)
    product_out_ids = fields.One2many("mrp.simple.line.out", "mrp_simple_id", string="Consumed products", copy=True)

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

    sale_order_id = fields.Many2one("sale.order", string="Sale Order", copy=False)
    # advanced simple production
    auto_create_sale = fields.Boolean("Create product & sale", default=False, copy=False)
    partner_id = fields.Many2one("res.partner", string="Client", copy=False)
    final_product_name = fields.Char("Final product name", copy=False)
    final_product_qty = fields.Float(string="Quantity", digits="Product Unit of Measure", default=1, copy=False)
    final_product_category = fields.Many2one("product.category", string="Category for final product", copy=False)
    final_product_uom_id = fields.Many2one("uom.uom", "Unit of Measure", copy=False)

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

        self.create_sale()
        self.create_picking_lines_in(picking_in)
        self.create_picking_lines_out(picking_out)

        # adaugare picking ids in sale order
        if self.sale_order_id:
            self.sale_order_id.update({"simple_mrp_picking_ids": [(4, picking_in.id, False)]})
            self.sale_order_id.update({"simple_mrp_picking_ids": [(4, picking_out.id, False)]})

        self.consume_id = picking_out
        self.receipt_id = picking_in

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

        self.write({"state": "done"})
        return self

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

    def create_final_product(self):
        if self.final_product_name:
            standard_price, list_price = self.get_final_product_prices()
            vals = {
                "type": "product",
                "name": self.final_product_name,
                "categ_id": self.final_product_category.id,
                "standard_price": standard_price,
                "list_price": list_price,
                "uom_id": self.final_product_uom_id.id,
            }
            product = self.env["product.product"].create(vals)
            return product.id
        else:
            return False

    def get_final_product_prices(self):
        standard_price = 0.0
        list_price = 0.0
        for line in self.product_out_ids:
            standard_price += line.product_id.standard_price * line.quantity
            list_price += line.product_id.lst_price * line.quantity
        standard_price = standard_price / self.final_product_qty
        list_price = list_price / self.final_product_qty
        return standard_price, list_price

    def create_sale(self):
        # adaugare picking ids in sale order
        if self.auto_create_sale:
            product_id = self.create_final_product()
            if not product_id:
                raise UserError(_("Error creating final product!"))
            standard_price = 0.0
            for line in self.product_out_ids:
                standard_price += line.price_unit * line.quantity
            standard_price = standard_price / self.final_product_qty
            vals = {
                "mrp_simple_id": self.id,
                "product_id": product_id,
                "quantity": self.final_product_qty,
                "price_unit": standard_price,
                "uom_id": self.final_product_uom_id.id,
            }
            self.product_in_ids.create(vals)

            vals = {
                "partner_id": self.partner_id.id,
            }
            sale_order = self.env["sale.order"].create(vals)
            vals = {
                "order_id": sale_order.id,
                "product_id": product_id,
                "product_uom_qty": self.final_product_qty,
                "product_uom": self.final_product_uom_id.id,
            }
            sale_order.order_line.create(vals)
            self.sale_order_id = sale_order

    def open_consume(self):
        self.ensure_one()
        return {
            "res_id": self.consume_id.id,
            "target": "current",
            "name": _("Consume"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.picking",
            "view_id": self.env.ref("stock.view_picking_form").id,
            "context": {},
            "type": "ir.actions.act_window",
        }

    def open_receipt(self):
        self.ensure_one()
        return {
            "res_id": self.receipt_id.id,
            "target": "current",
            "name": _("Receipt"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.picking",
            "view_id": self.env.ref("stock.view_picking_form").id,
            "context": {},
            "type": "ir.actions.act_window",
        }

    def compute_finit_price(self):
        self.ensure_one()
        finit_price = 0.0
        for line in self.product_out_ids:
            finit_price += line.value
        for line in self.product_in_ids:
            line.price_unit = finit_price / line.quantity

    def create_picking_lines_in(self, picking_in):
        if not self.product_in_ids:
            raise UserError(_("You need at least one final product"))
        for line in self.product_in_ids:
            params = self.env["ir.config_parameter"].sudo()
            allow_zero = params.get_param("deltatech_mrp_simple.allow_zero_cost", False)
            if not line.price_unit and not allow_zero:
                raise UserError(_("Price 0 for result product!"))
            if line.product_id.type != "service":
                self.add_picking_line(
                    picking=picking_in,
                    product=line.product_id,
                    quantity=line.quantity,
                    uom=line.uom_id,
                    price_unit=line.price_unit,
                )

    def create_picking_lines_out(self, picking_out):
        for line in self.product_out_ids:
            if line.product_id.type != "service":
                self.add_picking_line(
                    picking=picking_out,
                    product=line.product_id,
                    quantity=line.quantity,
                    uom=line.uom_id,
                    price_unit=line.product_id.standard_price,
                )


class MRPSimpleLineIn(models.Model):
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


class MRPSimpleLineOut(models.Model):
    _name = "mrp.simple.line.out"
    _description = "MRP Simple Line OUT"

    mrp_simple_id = fields.Many2one("mrp.simple")
    product_id = fields.Many2one("product.product")
    quantity = fields.Float(string="Quantity", digits="Product Unit of Measure", default=1)
    price_unit = fields.Float("Unit Price", digits="Product Price")
    uom_id = fields.Many2one("uom.uom", "Unit of Measure")
    stock = fields.Float(related="product_id.qty_available")
    value = fields.Float(compute="_compute_value", string="Value", store=True)

    @api.depends("quantity", "price_unit")
    def _compute_value(self):
        for line in self:
            line.value = line.quantity * line.price_unit

    @api.onchange("product_id", "quantity")
    def onchange_product_id(self):
        self.uom_id = self.product_id.uom_id
        self.price_unit = self.product_id.standard_price
