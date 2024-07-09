# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

# flux garantii


class ServiceWarranty(models.Model):
    _name = "service.warranty"
    _description = "Warranty"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Reference", readonly=True, index=True, default="/", copy=False)
    date = fields.Datetime(
        string="Date", default=fields.Date.context_today, readonly=True, states={"new": [("readonly", False)]}
    )
    state = fields.Selection(
        [
            ("new", "New"),
            ("assigned", "Assigned"),
            ("progress", "In Progress"),
            ("approval_requested", "Approval requested"),
            ("approved", "Approved"),
            ("done", "Done"),
        ],
        default="new",
        string="Status",
        tracking=True,
    )
    equipment_id = fields.Many2one(
        "service.equipment", string="Equipment", index=True, readonly=True, states={"new": [("readonly", False)]}
    )
    partner_id = fields.Many2one("res.partner", string="Customer")
    user_id = fields.Many2one("res.users", string="Responsible")
    description = fields.Text("Notes", readonly=False, states={"done": [("readonly", True)]})
    picking_id = fields.Many2one("stock.picking", string="Consumables", copy=False)
    sale_order_id = fields.Many2one("sale.order", string="Sale Order")
    invoice_id = fields.Many2one("account.move", string="Invoice")
    item_ids = fields.One2many(
        "service.warranty.item",
        "warranty_id",
        string="Warranty Lines",
        readonly=False,
        states={"done": [("readonly", True)]},
        copy=True,
    )

    @api.onchange("equipment_id")
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.user_id = self.equipment_id.technician_user_id or self.user_id
            if self.equipment_id.serial_id:
                moves = self.env["stock.move"].search(
                    [("lot_ids", "in", self.equipment_id.serial_id.ids), ("state", "=", "done")], order="date DESC"
                )
                if moves:
                    last_move = False
                    if moves[0].location_dest_usage == "customer":
                        # if last move seems like a delivery
                        last_move = moves[0]
                    else:
                        for move in moves:
                            if move.location_dest_usage == "customer":
                                last_move = move
                                break
                    if last_move and last_move.sale_line_id:
                        self.sale_order_id = last_move.sale_line_id.order_id
                        invoice_lines = last_move.sale_line_id.invoice_lines
                        invoices = invoice_lines.move_id
                        if len(invoices) == 1:
                            if invoices.state == "posted" and invoices.move_type == "out_invoice":
                                self.invoice_id = invoices
                                self.partner_id = invoices.partner_id
        else:
            self.invoice_id = False
            self.sale_order_id = False
            self.partner_id = False

    def new_delivery_button(self):
        # block picking if partner blocked
        if self.partner_id:
            if self.partner_id.picking_warn == "block":
                raise UserError(self.partner_id.picking_warn_msg)
            if self.partner_id.parent_id:
                if self.partner_id.parent_id.picking_warn == "block":
                    raise UserError(self.partner_id.parent_id.picking_warn_msg)

        get_param = self.env["ir.config_parameter"].sudo().get_param
        picking_type_id = safe_eval(get_param("service.picking_type_for_warranty", "False"))
        if picking_type_id:
            picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        else:
            raise UserError(_("Please set a warranty picking type in settings"))

        # context = self.get_context_default()
        context = dict(self.env.context)
        context.update(
            {
                "default_origin": self.name,
                "default_picking_type_code": "outgoing",
                "default_picking_type_id": picking_type_id,
                "default_partner_id": self.partner_id.id,
            }
        )

        if self.item_ids:
            context["default_move_ids_without_package"] = []

            for item in self.item_ids:
                value = {
                    "name": item.product_id.name,
                    "product_id": item.product_id.id,
                    "product_uom": item.product_id.uom_id.id,
                    "product_uom_qty": item.quantity,
                    "location_id": picking_type.default_location_src_id.id,
                    "location_dest_id": picking_type.default_location_dest_id.id,
                    "price_unit": item.product_id.standard_price,
                }
                context["default_move_ids_without_package"] += [(0, 0, value)]
        context["warranty_id"] = self.id
        return {
            "name": _("Delivery for warranty"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.picking",
            "view_id": False,
            "views": [[False, "form"]],
            "context": context,
            "type": "ir.actions.act_window",
        }

    @api.onchange("user_id")
    def set_assigned(self):
        if self.state == "new" and self.user_id:
            self.state = "assigned"
            if self.name == "/":
                self.name = self.env["ir.sequence"].next_by_code("service.warranty")

    def set_new(self):
        if self.state == "assigned":
            self.state = "new"
            self.user_id = False
            if self.name == "/":
                self.name = self.env["ir.sequence"].next_by_code("service.warranty")

    def set_in_progress(self):
        if self.state == "assigned" and self.user_id:
            self.state = "progress"
            if self.name == "/":
                self.name = self.env["ir.sequence"].next_by_code("service.warranty")

    def request_approval(self):
        self.state = "approval_requested"

    def approve(self):
        self.state = "approved"

    def set_done(self):
        self.state = "done"


class ServiceWarrantyItem(models.Model):
    _name = "service.warranty.item"
    _description = "Warranty Item"
    _order = "warranty_id, sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    name = fields.Char("Name")
    warranty_id = fields.Many2one(
        "service.warranty", string="Warranty", readonly=True, index=True, required=True, ondelete="cascade"
    )
    product_id = fields.Many2one("product.product", string="Product")
    alternative_code = fields.Char(related="product_id.alternative_code")
    quantity = fields.Float(string="Quantity", digits="Product Unit of Measure", default=1)
    product_uom = fields.Many2one("uom.uom", string="Unit of Measure ")
    note = fields.Char(string="Note")

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.product_uom = self.product_id.uom_id
        self.name = self.product_id.name
