# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

# flux garantii si reconditionari


class ServiceWarranty(models.Model):
    _name = "service.warranty"
    _description = "Warranty"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    type = fields.Selection([("warranty", "Warranty"), ("recondition", "Recondition")])
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

    rec_state = fields.Selection(
        [
            ("new", "New"),
            ("progress", "In Progress"),
            ("done", "Done"),
        ],
        default="new",
        string="Status",
        tracking=True,
    )

    clarifications_state = fields.Selection(
        [("required", "Required"), ("sent", "Sent")], string="Clarifications", tracking=True
    )
    equipment_id = fields.Many2one("service.equipment", string="Equipment", index=True, readonly=True)
    partner_id = fields.Many2one("res.partner", string="Customer")
    has_agreement = fields.Boolean("Has service agreement", compute="_compute_service_agreement")
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
    total_amount = fields.Float(string="Total amount", compute="_compute_total_amount", store=True)

    def _compute_service_agreement(self):
        agreements_installed = (
            self.env["ir.module.module"]
            .sudo()
            .search([("name", "=", "deltatech_service_agreement"), ("state", "=", "installed")])
        )
        for warranty in self:
            if not agreements_installed:
                warranty.has_agreement = False
            else:
                query = """
                                    SELECT id, state FROM service_agreement agr
                                    WHERE
                                        state IN %(states)s
                                        AND partner_id IN %(partners)s
                                """
                params = {
                    "partners": tuple([warranty.partner_id.id, warranty.partner_id.commercial_partner_id.id]),
                    "states": tuple(["draft", "open"]),
                }
                self.env.cr.execute(query, params=params)
                res = self.env.cr.dictfetchall()
                if res:
                    warranty.has_agreement = True
                else:
                    warranty.has_agreement = False

    @api.depends("item_ids")
    def _compute_total_amount(self):
        for warranty in self:
            total_amount = 0.0
            for line in warranty.item_ids:
                total_amount += line.amount
            warranty.total_amount = total_amount

    @api.onchange("equipment_id")
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.user_id = self.equipment_id.technician_user_id or self.user_id
            if self.equipment_id.serial_id:
                move_lines = (
                    self.env["stock.move.line"]
                    .sudo()
                    .search(
                        [
                            ("lot_id", "=", self.equipment_id.serial_id.id),
                            ("state", "=", "done"),
                            ("product_id", "=", self.equipment_id.product_id.id),
                        ],
                        order="date DESC",
                    )
                )
                if move_lines:
                    last_move = False
                    if move_lines[0].location_dest_id.usage == "customer":
                        # if last move seems like a delivery
                        last_move = move_lines[0]
                    else:
                        for move in move_lines:
                            if move.location_dest_id.usage == "customer":
                                last_move = move
                                break
                    if last_move and last_move.sudo().move_id.sale_line_id:
                        self.sudo().sale_order_id = last_move.move_id.sudo().sale_line_id.order_id
                        invoice_lines = last_move.move_id.sudo().sale_line_id.invoice_lines
                        invoices = invoice_lines.sudo().move_id
                        if len(invoices.sudo()) == 1:
                            if invoices.sudo().state == "posted" and invoices.sudo().move_type == "out_invoice":
                                self.invoice_id = invoices.sudo()
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
            self.with_context(change_ok=True).write({"state": "assigned"})
            if self.name == "/":
                self.name = self.env["ir.sequence"].next_by_code("service.warranty")

    def set_new(self):
        if self.state == "assigned":
            self.with_context(change_ok=True).write({"state": "new"})
            self.user_id = False
            if self.name == "/":
                self.name = self.env["ir.sequence"].next_by_code("service.warranty")

    def set_in_progress(self):
        if self.state == "assigned" and self.user_id:
            self.with_context(change_ok=True).write({"state": "progress"})

    def request_approval(self):
        self.with_context(change_ok=True).write({"state": "approval_requested"})

    def approve(self):
        self.with_context(change_ok=True).write({"state": "approved"})

    def set_done(self):
        self.with_context(change_ok=True).write({"state": "done"})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if "name" not in vals or ("name" in vals and vals["name"] == "/"):
                vals["name"] = self.env["ir.sequence"].next_by_code("service.warranty")
        return super().create(vals_list)

    def write(self, vals):
        if (
            "state" in vals
            and vals["state"]
            and not self.env.context.get("change_ok", False)
            and self.state not in ["new"]
            and not self.env.user.has_group("deltatech_service.group_warranty_manager")
        ):
            raise UserError(_("Your user cannot change the state directly"))
        return super().write(vals)


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
    price_unit = fields.Float(string="Unit price")
    amount = fields.Float(string="Amount", compute="_compute_amount")

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.product_uom = self.product_id.uom_id
        self.name = self.product_id.name
        self.price_unit = self.product_id.standard_price

    def _compute_amount(self):
        for line in self:
            line.amount = line.price_unit * line.quantity
