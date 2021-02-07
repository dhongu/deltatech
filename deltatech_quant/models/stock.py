# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class StockQuantTag(models.Model):
    _name = "stock.quant.tag"
    _description = "Stock Quant Tag"

    name = fields.Char(string="Name")


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if "invoice_id" in vals:
            for picking in self:
                for move in picking.move_lines:
                    if move.location_id.usage == "supplier":
                        move.quant_ids.write({"invoice_id": vals["invoice_id"]})

        return res


class StockQuant(models.Model):
    _inherit = "stock.quant"

    inventory_value = fields.Float(store=True)
    categ_id = fields.Many2one(
        "product.category", string="Internal Category", related="product_id.categ_id", store=True, readonly=True
    )

    # Campuri  din versiunea 10
    input_price = fields.Float(string="Input Price")
    output_price = fields.Float(string="Output Price")
    input_date = fields.Date(string="Input date")  # exista deja un camp care se cheama in_date nu o fi bun ala ?
    output_date = fields.Date(string="Output date")
    input_amount = fields.Float(string="Input Amount", compute="_compute_input_amount", store=True)
    output_amount = fields.Float(string="Output Amount", compute="_compute_output_amount", store=True)

    customer_id = fields.Many2one("res.partner", string="Customer")
    supplier_id = fields.Many2one("res.partner", string="Supplier")
    origin = fields.Char(string="Source Document")
    invoice_id = fields.Many2one("account.move", string="Invoice")  # de vanzare

    note = fields.Char(string="Note")
    tag_ids = fields.Many2many("stock.quant.tag", "stock_quant_tags", "quant_id", "tag_id", string="Tags")

    def _compute_name(self):
        super(StockQuant, self)._compute_name()
        if self.supplier_id:
            self.name = "[" + self.supplier_id.name + "]" + self.name

    def update_input_output(self):
        for quant in self:
            quant.history_ids.update_quant_partner()
            quant._compute_input_amount()
            quant._compute_output_amount()

    def update_all_input_output(self):
        quants = self.search([])
        quants.update_input_output()

    @api.depends("input_price", "quantity")
    def _compute_input_amount(self):
        for quant in self:
            quant.input_amount = quant.input_price * quant.quantity

    @api.depends("output_price", "quantity")
    def _compute_output_amount(self):
        for quant in self:
            quant.output_amount = quant.output_price * quant.quantity


class StockMove(models.Model):
    _inherit = "stock.move"

    def update_quant_partner(self):
        pos_mod = self.env["ir.module.module"].search([("name", "=", "point_of_sale"), ("state", "=", "installed")])

        for move in self:

            if move.picking_id:

                value = {"origin": move.picking_id.origin}
                if move.location_dest_id.usage == "customer" and move.location_id.usage in ["internal", "supplier"]:
                    if move.picking_id.partner_id:
                        value["customer_id"] = move.picking_id.partner_id.id
                    value["output_date"] = move.date  # move.picking_id.date_done
                    price_invoice = move.price_unit
                    sale_line = move.procurement_id.sale_line_id
                    if sale_line:
                        price_invoice = sale_line.price_subtotal / sale_line.product_uom_qty
                        price_invoice = (
                            sale_line.order_id.company_id.currency_id._get_conversion_rate(
                                sale_line.order_id.currency_id, move.company_id.currency_id
                            )
                            * price_invoice
                        )
                    else:
                        # Vanzare din POS
                        if pos_mod:
                            pos_order = self.env["pos.order"].search([("picking_id", "=", move.picking_id.id)])
                            if pos_order:
                                for line in pos_order.lines:
                                    if line.product_id == move.product_id:
                                        price_invoice = line.price_subtotal / line.qty
                    value["output_price"] = price_invoice

                if move.location_id.usage == "supplier" and move.location_dest_id.usage in ["internal", "customer"]:
                    if move.picking_id.partner_id:
                        value["supplier_id"] = move.picking_id.partner_id.id
                    if move.invoice_line_id:
                        value["invoice_id"] = move.invoice_line_id.invoice_id.id
                    value["input_date"] = move.date  # move.picking_id.date_done
                    value["input_price"] = move.price_unit

                if move.location_id.usage == "inventory" and move.location_dest_id.usage == "internal":
                    value["input_date"] = move.date  # move.picking_id.date_done
                    value["input_price"] = move.price_unit
                    if not move.price_unit and move.product_id.seller_ids:
                        value["input_price"] = move.product_id.seller_ids[0].price

                if value:
                    move.quant_ids.write(value)

    def action_done(self):
        res = super(StockMove, self).action_done()
        self.update_quant_partner()
        return res

    def show_picking(self):
        self.ensure_one()
        if self.picking_id:
            return {
                "type": "ir.actions.act_window",
                "res_model": "stock.picking",
                "view_mode": "form",
                "res_id": self.picking_id.id,
            }

    def show_invoice(self):
        self.ensure_one()
        if self.picking_id:
            if self.picking_id.invoice_id:
                return {
                    "type": "ir.actions.act_window",
                    "res_model": "account.invoice",
                    "view_mode": "form",
                    "res_id": self.picking_id.invoice_id.id,
                }
