# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import uuid

from odoo import _, api, fields, models
from odoo.exceptions import UserError

# raport de activitate
# nota de constatare


class ServiceOrder(models.Model):
    _name = "service.order"
    _description = "Service Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"

    name = fields.Char(string="Reference", readonly=True, index=True, default=lambda self: _("New"))
    date = fields.Date(
        string="Date", default=fields.Date.context_today, readonly=True, states={"draft": [("readonly", False)]}
    )

    access_token = fields.Char(string="Security Token", required=True, copy=False, default=str(uuid.uuid4()))

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("acknowledge", "Acknowledge"),
            ("on_way", "On the way"),
            ("progress", "In Progress"),
            ("work_done", "Work Done"),
            ("rejected", "Rejected"),
            ("cancel", "Cancel"),
            ("done", "Completed"),
        ],
        default="draft",
        string="Status",
    )

    date_start_travel = fields.Datetime("Start Travel Date", readonly=True, copy=False)
    date_start = fields.Datetime("Start Date", readonly=True, copy=False, states={"progress": [("readonly", False)]})
    date_done = fields.Datetime("Done Date", readonly=True, copy=False, states={"work_done": [("readonly", False)]})

    # equipment_history_id = fields.Many2one("service.equipment.history", string="Equipment history")
    equipment_id = fields.Many2one(
        "service.equipment",
        string="Equipment",
        index=True,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )

    partner_id = fields.Many2one(
        "res.partner", string="Partner", readonly=True, states={"draft": [("readonly", False)]}
    )

    contact_id = fields.Many2one(
        "res.partner", string="Contact person", tracking=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    address_id = fields.Many2one(
        "res.partner", string="Location", readonly=True, states={"draft": [("readonly", False)]}
    )
    city = fields.Char(string="City", related="address_id.city")

    user_id = fields.Many2one("res.users", string="Responsible", readonly=True, states={"draft": [("readonly", False)]})

    work_center_id = fields.Many2one(
        "service.work.center", string="Work Center", readonly=True, states={"draft": [("readonly", False)]}
    )

    # raportul poate sa fie legat de o sesizre
    notification_id = fields.Many2one(
        "service.notification",
        string="Notification",
        readonly=True,
        states={"draft": [("readonly", False)]},
        domain=[("order_id", "=", False)],
    )

    reason_id = fields.Many2one(
        "service.order.reason", string="Reason", readonly=False, states={"done": [("readonly", True)]}
    )
    type_id = fields.Many2one(
        "service.order.type", string="Type", required=True, readonly=True, states={"draft": [("readonly", False)]}
    )
    with_travel = fields.Boolean(related="type_id.with_travel")
    can_delivered = fields.Boolean(related="type_id.can_delivered")
    can_ordered = fields.Boolean(related="type_id.can_ordered")

    parameter_ids = fields.Many2many(
        "service.operating.parameter",
        "service_order_agreement",
        "order_id",
        "parameter_id",
        string="Parameter",
        readonly=False,
        states={"done": [("readonly", True)], "cancel": [("readonly", True)]},
    )

    component_ids = fields.One2many(
        "service.order.component",
        "order_id",
        string="Order Components",
        readonly=False,
        states={"done": [("readonly", True)]},
        copy=True,
    )

    operation_ids = fields.One2many(
        "service.order.operation",
        "order_id",
        string="Order Operations",
        readonly=False,
        states={"done": [("readonly", True)]},
        copy=True,
    )

    # semantura client !!
    signature = fields.Binary(string="Signature", readonly=True)

    description = fields.Text("Notes", readonly=False, states={"done": [("readonly", True)]})

    @api.model
    def create(self, vals):
        if vals.get("name", _("New")) == _("New"):
            seq_date = None
            if "date" in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals["date"]))
            vals["name"] = self.env["ir.sequence"].next_by_code("service.order", sequence_date=seq_date) or _("New")
        return super(ServiceOrder, self).create(vals)

    @api.onchange("equipment_id", "date")
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.user_id = self.equipment_id.technician_user_id or self.user_id
            self.partner_id = self.equipment_id.partner_id
            # self.address_id = self.equipment_id.address_id

    @api.onchange("notification_id")
    def onchange_notification_id(self):
        if self.notification_id:
            self.equipment_id = self.notification_id.equipment_id
            self.notification_id.order_id = self  # oare e bine ?

    def action_cancel(self):
        self.write({"state": "cancel"})

    def action_rejected(self):
        self.write({"state": "rejected"})

    def action_acknowledge(self):
        self.write({"state": "acknowledge"})

    def action_start_on_way(self):
        self.write({"state": "on_way", "date_start_travel": fields.Datetime.now()})

    def action_start(self):
        value = {"state": "progress", "date_start": fields.Datetime.now()}

        self.write(value)
        for order in self:
            if not order.date_start_travel:
                order.write({"date_start_travel": fields.Datetime.now()})

    def action_work_again(self):
        self.write({"state": "progress"})

    def action_work_done(self):
        if self.signature:
            self.write({"date_done": fields.Datetime.now()})
            self.action_done()
        else:
            self.write({"state": "work_done", "date_done": fields.Datetime.now()})

    def action_done(self):
        if not self.parameter_ids and not self.signature:
            raise UserError(_("Please select a parameter."))
        self.write({"state": "done"})

        if self.notification_id:
            self.notification_id.action_done()

    def new_piking_button(self):
        if self.equipment_id:
            return self.equipment_id.new_piking_button()

    def sale_order_button(self):
        action = self.get_action_sale_order()
        if action["res_id"]:
            return action

    def get_action_sale_order(self):
        sale_order = self.env["sale.order"].search([("service_order_id", "=", self.id)])
        if not sale_order and self.notification_id:
            sale_order = self.env["sale.order"].search([("notification_id", "=", self.notification_id.id)])
            sale_order.write({"service_order_id": self.id})

        action = {
            "name": _("Sale Order for Service Order"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sale.order",
            "view_id": False,
            "views": [[False, "form"]],
            "context": {},
            "type": "ir.actions.act_window",
            "res_id": sale_order.id,
        }
        return action

    def new_sale_order_button(self):
        if self.partner_id.sale_warn and self.partner_id.sale_warn == "block":
            raise UserError(_("This partner is blocked"))

        action = self.get_action_sale_order()
        context = {
            "default_partner_id": self.partner_id.id,
            "default_partner_shipping_id": self.address_id.id,
            "default_service_order_id": self.id,
            "default_notification_id": self.notification_id.id,
        }

        route = self.work_center_id.sale_route_id

        if action["res_id"]:
            sale_order = self.env["sale.order"].browse(action["res_id"])

            for item in self.component_ids:
                sale_line = sale_order.order_line.filtered(lambda l: l.product_id == item.product_id)
                if not sale_line:
                    value = {
                        "product_id": item.product_id.id,
                        "product_uom_qty": item.quantity,
                        "route_id": route.id,
                        "state": "draft",
                        "order_id": sale_order.id,
                    }
                    self.env["sale.order.line"].create(value)
                else:
                    sale_line.write({"product_uom_qty": item.quantity})
        else:

            context["pricelist_id"] = self.partner_id.property_product_pricelist.id
            sale_order = self.env["sale.order"].with_context(context).new()

            context["default_order_line"] = []
            for item in self.component_ids:
                value = {
                    "product_id": item.product_id.id,
                    "product_uom_qty": item.quantity,
                    "route_id": route.id,
                    "state": "draft",
                    "order_id": sale_order.id,
                }
                line = self.env["sale.order.line"].new(value)
                line.product_id_change()
                for field in ["name", "price_unit", "product_uom", "tax_id"]:
                    value[field] = line._fields[field].convert_to_write(line[field], line)

                context["default_order_line"] += [(0, 0, value)]

        action["context"] = context
        return action

    def unlink(self):
        for order in self:
            if order.state not in ["draft", "cancel"]:
                raise UserError(_("Can not delete order in status %s") % order.state)
        return super(ServiceOrder, self).unlink()

    def open_order_on_website(self):
        url = "/service/order/" + str(self.id)
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }


class ServiceOrderComponent(models.Model):
    _name = "service.order.component"
    _description = "Service Order Component"
    _order = "order_id, sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)
    name = fields.Char()
    order_id = fields.Many2one(
        "service.order", string="Order", readonly=True, index=True, required=True, ondelete="cascade"
    )
    product_id = fields.Many2one("product.product", string="Product", domain=[("type", "!=", "service")])
    quantity = fields.Float(string="Quantity", digits="Product Unit of Measure", default=1)
    product_uom = fields.Many2one("uom.uom", string="Unit of Measure ")
    note = fields.Char(string="Note")

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.product_uom = self.product_id.uom_id
        self.name = self.product_id.name


class ServiceOrderOperation(models.Model):
    _name = "service.order.operation"
    _description = "Service Order Operation"
    _order = "order_id, sequence, id"

    sequence = fields.Integer(string="Sequence", default=10)

    order_id = fields.Many2one(
        "service.order", string="Order", readonly=True, index=True, required=True, ondelete="cascade"
    )
    operation_id = fields.Many2one("service.operation", string="Operation")
    duration = fields.Float(string="Duration")

    @api.onchange("operation_id")
    def onchange_operation_id(self):
        self.duration = self.operation_id.duration


class ServiceOrderReason(models.Model):
    _name = "service.order.reason"
    _description = "Service Order Reason"

    name = fields.Char(string="Reason", translate=True)
    code = fields.Char(string="Code")
    display_name = fields.Char(compute="_compute_display_name")

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, self.display_name))
        return result

    @api.depends("name", "code")  # this definition is recursive
    def _compute_display_name(self):
        for reason in self:
            if reason.code:
                reason.display_name = "[{}] {}".format(reason.code, reason.name)
            else:
                reason.display_name = reason.name


class ServiceOperatingParameter(models.Model):
    _name = "service.operating.parameter"
    _description = "Service Operating Parameter"
    name = fields.Char(string="Parameter", translate=True)


class ServiceOrderType(models.Model):
    _name = "service.order.type"
    _description = "Service Order Type"

    name = fields.Char(string="Type", translate=True)
    category = fields.Selection([("cor", "Corrective"), ("pre", "Preventive")])

    with_travel = fields.Boolean()
    can_delivered = fields.Boolean()
    can_ordered = fields.Boolean()


class ServiceOperation(models.Model):
    _name = "service.operation"
    _description = "Service Operation"

    name = fields.Char(string="Operation")
    code = fields.Char(string="Code")
    duration = fields.Float(string="Duration")
    display_name = fields.Char(compute="_compute_display_name")
    product_id = fields.Many2one("product.product", domain=[("type", "=", "service")])

    def name_get(self):
        result = []
        for record in self:
            result.append((record.id, record.display_name))
        return result

    @api.depends("name", "code")  # this definition is recursive
    def _compute_display_name(self):
        for operation in self:
            if operation.code:
                operation.display_name = "[{}] {}".format(operation.code, operation.name)
            else:
                operation.display_name = operation.name
