# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError

# sesizari primite din partea clientilor

# todo: de  definit in configurare o adresa in care se introduc sesizarile de service
# la creare se incearca o determinare a echipamentului

AVAILABLE_PRIORITIES = [
    ("0", "Very Low"),
    ("1", "Low"),
    ("2", "Normal"),
    ("3", "High"),
    ("4", "Very High"),
]


class ServiceNotification(models.Model):
    _name = "service.notification"
    _description = "Notification"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    def compute_default_user_id(self):
        return self.env.user.id

    name = fields.Char(string="Reference", readonly=True, default="/")
    date = fields.Datetime(
        string="Date", default=fields.Datetime.now, readonly=True, states={"new": [("readonly", False)]}
    )

    state = fields.Selection(
        [("new", "New"), ("assigned", "Assigned"), ("progress", "In Progress"), ("done", "Done")],
        default="new",
        string="Status",
        track_visibility="always",
    )

    equipment_history_id = fields.Many2one("service.equipment.history", string="Equipment history")
    equipment_id = fields.Many2one(
        "service.equipment", string="Equipment", index=True, readonly=True, states={"new": [("readonly", False)]}
    )

    partner_id = fields.Many2one(
        "res.partner", string="Partner", readonly=True, states={"new": [("readonly", False)]}
    )  # , related='equipment_history_id.partner_id', readonly=True)
    address_id = fields.Many2one(
        "res.partner", string="Location", readonly=True, states={"new": [("readonly", False)]}
    )  # ,  related='equipment_history_id.address_id', readonly=True)
    emplacement = fields.Char(
        string="Emplacement",
        # related="equipment_history_id.emplacement",
        related=False,
        readonly=True,
    )
    agreement_id = fields.Many2one(
        "service.agreement", string="Service Agreement", related="equipment_history_id.agreement_id", readonly=True
    )

    contact_id = fields.Many2one(
        "res.partner",
        string="Reported by",
        help="The person who reported the notification",
        default=lambda self: self.env.user.partner_id,
        readonly=True,
        states={"new": [("readonly", False)]},
    )

    user_id = fields.Many2one("res.users", string="Responsible", readonly=True, states={"new": [("readonly", False)]})

    type = fields.Selection(
        [("external", "External"), ("internal", "Internal")],
        default="external",
        string="Type",
        readonly=True,
        states={"new": [("readonly", False)]},
    )

    subject = fields.Char("Subject", readonly=True, states={"new": [("readonly", False)]})
    description = fields.Text("Notes", readonly=True, states={"new": [("readonly", False)]})

    date_assing = fields.Datetime("Assigning Date", readonly=True, copy=False)
    date_start = fields.Datetime("Start Date", readonly=True, copy=False)
    date_done = fields.Datetime("Done Date", readonly=True, copy=False)

    priority = fields.Selection(
        AVAILABLE_PRIORITIES, string="Priority", index=True, readonly=True, states={"new": [("readonly", False)]}
    )
    color = fields.Integer(string="Color Index", default=0)
    order_id = fields.Many2one("service.order", string="Order", readonly=True, copy=False, compute="_compute_order_id")

    category = fields.Selection(
        [
            ("sale_support", "Sale Support"),
            ("delivery", "Delivery"),
            ("sale", "Sale"),
            ("transfer", "Transfer"),
            ("required", "Required"),
        ],
        default="sale_support",
        string="Category",
    )

    piking_id = fields.Many2one("stock.picking", string="Consumables")  # legatua cu necesarul / consumul de consumabile
    sale_order_id = fields.Many2one("sale.order", string="Sale Order")  # legatua la comanda de vanzare
    required_order_id = fields.Many2one("required.order", string="Required Products Order")

    related_doc = fields.Boolean(_compute="_get_related_doc")

    item_ids = fields.One2many(
        "service.notification.item",
        "notification_id",
        string="Notification Lines",
        readonly=False,
        states={"done": [("readonly", True)]},
        copy=True,
    )

    def _get_related_doc(self):
        self.related_doc = False
        if self.piking_id or self.sale_order_id or self.required_order_id:
            return True

    @api.model
    def company_user(self, present_ids, domain, **kwargs):
        partner_id = self.env.user.company_id.partner_id
        users = self.env["res.users"].search([("partner_id.parent_id", "=", partner_id.id)])
        users_name = users.name_get()
        users_name.append((False, False))
        return users_name, None

    _group_by_full = {
        "user_id": company_user,
    }

    def _compute_order_id(self):
        self.order_id = self.env["service.order"].search([("notification_id", "=", self.id)], limit=1)

    @api.onchange("equipment_id", "date")
    def onchange_equipment_id(self):
        if self.equipment_id:
            self.equipment_history_id = self.equipment_id.get_history_id(self.date)
            self.user_id = self.equipment_id.user_id
            self.partner_id = self.equipment_history_id.partner_id
            self.address_id = self.equipment_history_id.address_id
        else:
            self.equipment_history_id = False

    @api.model
    def create(self, vals):

        equipment_id = vals.get("equipment_id", False)

        if not equipment_id:
            equipments = self.env["service.equipment"]
            contact_id = vals.get("contact_id", False)
            if contact_id:
                equipments = self.env["service.equipment"].search([("contact_id", "=", contact_id)])

            description = vals.get("description", False)

            if description and (len(equipments) != 1):
                keywords = description.split()
                equipments_by_ean = self.env["service.equipment"]
                for keyword in keywords:
                    equipments_by_ean |= self.env["service.equipment"].search([("ean_code", "=", keyword)])

                if len(equipments) == 0:
                    equipments = equipments_by_ean
                else:
                    equipments &= equipments_by_ean

            if len(equipments) == 1:
                vals["equipment_id"] = equipments.id
                if not vals.get("address_id", False):
                    vals["address_id"] = equipments.address_id.id
                if not vals.get("user_id", False):
                    vals["user_id"] = equipments.user_id.id
                if not vals.get("agreement_id", False):
                    vals["agreement_id"] = equipments.agreement_id.id
                if not vals.get("partner_id", False):
                    vals["partner_id"] = equipments.agreement_id.partner_id.id

        if ("name" not in vals) or (vals.get("name") in ("/", False)):
            sequence_notification = self.env.ref("deltatech_service_maintenance.sequence_notification")
            if sequence_notification:
                vals["name"] = self.env["ir.sequence"].next_by_id(sequence_notification.id)
        return super(ServiceNotification, self).create(vals)

    def write(self, vals):
        if "user_id" in vals:
            if self.state != "new":
                raise UserError(_("Notification is assigned."))
        result = super(ServiceNotification, self).write(vals)
        return result

    def action_cancel_assing(self):
        if self.state != "assigned":
            raise UserError(_("Notification is not assigned."))
        self.write({"state": "new", "date_assing": fields.Datetime.now()})

    def action_assing(self):
        if not self.user_id:
            raise UserError(_("Please select a responsible."))
        if self.state != "new":
            raise UserError(_("Notification is already assigned."))

        self.write({"state": "assigned", "date_assing": fields.Datetime.now()})

        new_follower_ids = [self.user_id.partner_id.id]

        if self.user_id != self.env.user.id:
            msg = _("Please solve notification for %s: %s") % (self.partner_id.name, self.description or "")

            if msg and not self.env.context.get("no_message", False):
                document = self
                message = self.env["mail.message"].with_context({"default_starred": True})
                message.create(
                    {
                        "model": "service.notification",
                        "res_id": document.id,
                        "record_name": document.name_get()[0][1],
                        "email_from": self.env["mail.message"]._get_default_from(),
                        "reply_to": self.env["mail.message"]._get_default_from(),
                        "subject": self.subject,
                        "body": msg,
                        "message_id": self.env["mail.message"]._get_message_id({"no_auto_thread": True}),
                        "partner_ids": [(4, id) for id in new_follower_ids],
                    }
                )

    def action_taking(self):
        if self.state != "new":
            raise UserError(_("Notification is already assigned."))
        self.message_mark_as_read()
        self.write({"state": "assigned", "date_assing": fields.Datetime.now(), "user_id": self.env.user.id})

    def action_start(self):
        # for notification in self:
        #    if not notification.partner_id:
        #        raise Warning(_('Notification %s without partner.') % notification.name )
        self.message_mark_as_read()
        self.write({"state": "progress", "date_start": fields.Datetime.now()})

    def action_order(self):
        context = {
            "default_notification_id": self.id,
            "default_equipment_id": self.equipment_id.id,
            "default_partner_id": self.partner_id.id,
            "default_agreement_id": self.agreement_id.id,
            "default_client_order_ref": self.name,
            "default_address_id": self.address_id.id,
            "default_contact_id": self.contact_id.id,
            "default_user_id": self.user_id.id,
        }

        if self.order_id:
            domain = "[('id','=', " + str(self.order_id.id) + ")]"
            res_id = self.order_id.id
        else:
            domain = "[]"
            res_id = False

        if self.partner_id.sale_warn and self.partner_id.sale_warn == "block":
            raise UserError(_("Acest partener este blocat"))
        else:
            return {
                "domain": domain,
                "res_id": res_id,
                "name": _("Services Order"),
                "view_type": "form",
                "view_mode": "form",
                "res_model": "service.order",
                "context": context,
                "type": "ir.actions.act_window",
            }

    def action_done(self):
        self.write({"state": "done", "date_done": fields.Datetime.now()})

        new_follower_ids = [self.contact_id.id]

        if self.user_id != self.env.user.id:
            msg = _("Notification %s for %s was done") % (self.description or "", self.partner_id.name)

            if msg and not self.env.context.get("no_message", False):
                document = self
                message = self.env["mail.message"].with_context({"default_starred": True})
                message.create(
                    {
                        "model": "service.notification",
                        "res_id": document.id,
                        "record_name": document.name_get()[0][1],
                        "email_from": self.env["mail.message"]._get_default_from(),
                        "reply_to": self.env["mail.message"]._get_default_from(),
                        "subject": self.subject,
                        "body": msg,
                        "message_id": self.env["mail.message"]._get_message_id({"no_auto_thread": True}),
                        "partner_ids": [(4, id) for id in new_follower_ids],
                    }
                )

                # TODO: De anuntat utilizatorul ca are o sesizare

    def new_delivery_button(self):
        context = {
            "default_equipment_id": self.equipment_id.id,
            "default_agreement_id": self.agreement_id.id,
            "default_origin": self.name,
            "default_picking_type_code": "outgoing",
            "default_picking_type_id": self.env.ref("stock.picking_type_outgoing_not2binvoiced").id,
            "default_partner_id": self.address_id.id or self.partner_id.id,
        }

        if self.item_ids:

            picking = self.env["stock.picking"].with_context(context)

            context["default_move_lines"] = []

            for item in self.item_ids:
                res = picking.move_lines.onchange_product_id(prod_id=item.product_id.id)
                value = res.get("value", {})
                value["location_id"] = picking.move_lines._default_location_source()
                value["location_dest_id"] = picking.move_lines._default_location_destination()
                value["date_expected"] = fields.Datetime.now()
                value["product_id"] = item.product_id.id
                value["product_uom_qty"] = item.quantity
                context["default_move_lines"] += [(0, 0, value)]
                context["notification_id"] = self.id
        return {
            "name": _("Delivery for service"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.picking",
            "view_id": False,
            "views": [[False, "form"]],
            "context": context,
            "type": "ir.actions.act_window",
        }

    def delivery_button(self):
        if self.piking_id:
            return {
                "domain": "[('id','=', [" + str(self.piking_id.id) + "])]",
                "name": _("Delivery for service"),
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "stock.picking",
                "view_id": False,
                "context": {},
                "type": "ir.actions.act_window",
            }

    def new_transfer_button(self):

        context = {
            # 'default_equipment_id': self.equipment_id.id,
            # 'default_agreement_id': self.agreement_id.id,
            "default_picking_type_code": "internal",
            "default_picking_type_id": self.env.ref("stock.picking_type_internal").id,
        }

        if self.item_ids:

            picking = self.env["stock.picking"].with_context(context)

            context["default_move_lines"] = []

            for item in self.item_ids:
                res = picking.move_lines.onchange_product_id(prod_id=item.product_id.id)
                value = res.get("value", {})

                value["location_id"] = picking.move_lines._default_location_source()
                value["location_dest_id"] = picking.move_lines._default_location_destination()
                value["date_expected"] = fields.Datetime.now()
                value["product_id"] = item.product_id.id
                value["product_uom_qty"] = item.quantity
                context["default_move_lines"] += [(0, 0, value)]
                context["notification_id"] = self.id
        return {
            "name": _("Transfer for service"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "stock.picking",
            "view_id": False,
            "views": [[False, "form"]],
            "context": context,
            "type": "ir.actions.act_window",
        }

    def transfer_button(self):
        if self.piking_id:
            return {
                "domain": "[('id','=', [" + str(self.piking_id.id) + "])]",
                "name": _("Transfer for service"),
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "stock.picking",
                "view_id": False,
                "context": {},
                "type": "ir.actions.act_window",
            }

    def new_sale_order_button(self):
        # todo: de pus in config daca livrarea se face la adresa din echipamente sau contract
        context = {"default_partner_id": self.partner_id.id, "default_partner_shipping_id": self.address_id.id}

        if self.item_ids:

            sale_order = self.env["sale.order"].with_context(context)
            pricelist = (
                self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False
            )
            context["default_order_line"] = []
            for item in self.item_ids:
                res = sale_order.order_line.product_id_change(
                    pricelist=pricelist, product=item.product_id.id, qty=item.quantity, partner_id=self.partner_id.id
                )
                value = res.get("value", {})
                value["product_id"] = item.product_id.id
                value["product_uom_qty"] = item.quantity
                value["state"] = "draft"
                context["default_order_line"] += [(0, 0, value)]
        context["notification_id"] = self.id
        if self.partner_id.sale_warn and self.partner_id.sale_warn == "block":
            raise UserError(_("This partner is blocked"))
        else:
            return {
                "name": _("Sale Order for Notification"),
                "view_type": "form",
                "view_mode": "form",
                "res_model": "sale.order",
                "view_id": False,
                "views": [[False, "form"]],
                "context": context,
                "type": "ir.actions.act_window",
            }

    def sale_order_button(self):
        if self.sale_order_id:
            return {
                "domain": "[('id','=', [" + str(self.sale_order_id.id) + "])]",
                "name": _("Sale Order for Notification"),
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "sale.order",
                "view_id": False,
                "context": {},
                "type": "ir.actions.act_window",
            }

    def new_required_order_button(self):
        context = {"default_partner_id": self.partner_id.id, "default_partner_shipping_id": self.address_id.id}
        if self.item_ids:
            context["default_required_line"] = []
            for item in self.item_ids:
                value = {}
                value["product_id"] = item.product_id.id
                value["product_qty"] = item.quantity
                value["note"] = item.note
                context["default_required_line"] += [(0, 0, value)]
                context["notification_id"] = self.id
        return {
            "name": _("Required Products Order for Notification"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "required.order",
            "view_id": False,
            "views": [[False, "form"]],
            "context": context,
            "type": "ir.actions.act_window",
        }

    def required_order_button(self):
        if self.required_order_id:
            return {
                "domain": "[('id','=', [" + str(self.required_order.id) + "])]",
                "name": _("Required Products Order for Notification"),
                "view_type": "form",
                "view_mode": "tree,form",
                "res_model": "required.order",
                "view_id": False,
                "context": {},
                "type": "ir.actions.act_window",
            }


class ServiceNotificationItem(models.Model):
    _name = "service.notification.item"
    _description = "Notification Item"

    notification_id = fields.Many2one("service.notification", string="Notification", readonly=True)
    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Float(string="Quantity", digits="Product Unit of Measure", default=1)
    product_uom = fields.Many2one("uom.uom", string="Unit of Measure ")
    note = fields.Char(string="Note")

    @api.onchange("product_id")
    def onchange_product_id(self):
        self.product_uom = self.product_id.uom_id


class ServiceNotificationType(models.Model):
    _name = "service.notification.type"
    _description = "Service Notification Type"
    name = fields.Char(string="Type", translate=True)
    scope = fields.Selection([("external", "External"), ("internal", "Internal")], default="external", string="Type")
