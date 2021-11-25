# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ServiceEquiOperation(models.TransientModel):
    _name = "service.equi.operation"
    _inherits = {"service.enter.reading": "enter_reading_id"}
    _description = "Service Equipment Operation"

    enter_reading_id = fields.Many2one(
        "service.enter.reading", string="Enter Reading", required=True, ondelete="cascade"
    )
    state = fields.Selection(
        [("ins", "Installation"), ("ebk", "Enable backup"), ("dbk", "Disable backup"), ("rem", "Removal")],
        string="Operation",
        default="ins",
        readonly=True,
    )
    equipment_id = fields.Many2one("service.equipment", string="Equipment", readonly=True)

    equipment_backup_id = fields.Many2one(
        "service.equipment", string="Backup Equipment", domain=[("state", "=", "available")]
    )

    partner_id = fields.Many2one("res.partner", string="Customer", domain=[("is_company", "=", True)])
    address_id = fields.Many2one("res.partner", string="Location")  # sa fac un nou tip de partener? locatie ?
    emplacement = fields.Char(string="Emplacement")
    stock_move = fields.Boolean(string="Stock Move", help="Generate stock move using setting from equipment category")

    @api.model
    def default_get(self, fields_list):
        defaults = super(ServiceEquiOperation, self).default_get(fields_list)

        active_id = self.env.context.get("active_id", False)
        if active_id:
            defaults["equipment_id"] = active_id
            equipment = self.env["service.equipment"].browse(active_id)
            defaults["partner_id"] = equipment.partner_id.id
            defaults["address_id"] = equipment.address_id.id
            defaults["emplacement"] = equipment.emplacement
        else:
            raise UserError(_("Please select equipment."))
        return defaults

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        self.address_id = self.partner_id

    @api.onchange("equipment_backup_id", "date")
    def onchange_equipment_backup_id(self):
        items = []
        for meter in self.equipment_id.meter_ids:
            if meter.type == "counter":
                meter = meter.with_context({"date": self.date})
                items += [
                    (
                        0,
                        0,
                        {
                            "meter_id": meter.id,
                            "equipment_id": meter.equipment_id.id,
                            "counter_value": meter.estimated_value,
                        },
                    )
                ]

        if self.equipment_backup_id:
            for meter in self.equipment_backup_id.meter_ids:
                if meter.type == "counter":
                    meter = meter.with_context({"date": self.date})
                    items += [
                        (
                            0,
                            0,
                            {
                                "meter_id": meter.id,
                                "equipment_id": meter.equipment_id.id,
                                "counter_value": meter.estimated_value,
                            },
                        )
                    ]

        items = self._convert_to_cache({"items": items}, validate=False)
        self.update(items)

    def do_operation(self):

        if self.equipment_id.equipment_history_id:
            if self.date < self.equipment_id.equipment_history_id.from_date:
                raise UserError(_("Date must be greater than %s") % self.equipment_id.equipment_history_id.from_date)

        values = {
            "equipment_id": self.equipment_id.id,
            "from_date": self.date,
            "partner_id": self.partner_id.id,
            "address_id": self.address_id.id,
            "emplacement": self.emplacement,
        }

        if self.state in ("rem", "dbk"):
            values["partner_id"] = False
            values["address_id"] = False
            values["emplacement"] = False

        if self.state == "ebk":
            values["equipment_backup_id"] = self.equipment_backup_id.id

        new_hist = self.env["service.equipment.history"].create(values)

        if self.state == "ins":
            self.equipment_id.write({"equipment_history_id": new_hist.id, "state": "installed"})
        elif self.state == "rem":
            self.equipment_id.write({"equipment_history_id": new_hist.id, "state": "available"})
        elif self.state == "ebk":
            self.equipment_id.write({"equipment_history_id": new_hist.id, "state": "backuped"})
            values["equipment_id"] = self.equipment_backup_id.id
            new_hist = self.env["service.equipment.history"].create(values)
            self.equipment_backup_id.write({"state": "installed", "equipment_history_id": new_hist.id})
        elif self.state == "dbk":
            self.equipment_id.write({"equipment_history_id": new_hist.id, "state": "installed"})
            values = {
                "equipment_id": self.equipment_backup_id.id,
                "from_date": self.date,
                "partner_id": False,
                "address_id": False,
                "emplacement": False,
            }
            new_hist = self.env["service.equipment.history"].create(values)
            self.equipment_backup_id.write({"state": "available", "equipment_history_id": new_hist.id})

        for item in self.items:
            self.env["service.meter.reading"].create(
                {
                    "meter_id": item.meter_id.id,
                    "equipment_id": item.meter_id.equipment_id.id,
                    "equipment_history_id": new_hist.id,
                    "date": self.date,
                    "read_by": self.read_by.id,
                    "note": self.note,
                    "counter_value": item.counter_value,
                }
            )

        action = True
        if self.stock_move and self.equipment_id.quant_id:
            context = {}
            if self.state == "ins" and self.equipment_id.type_id.categ_id.out_type_id:
                context = {
                    "default_picking_type_id": self.equipment_id.type_id.categ_id.out_type_id.id,
                    "default_partner_id": self.equipment_id.partner_id.id,
                }

            if self.state == "rem" and self.equipment_id.type_id.categ_id.in_type_id:
                context = {
                    "default_picking_type_id": self.equipment_id.type_id.categ_id.in_type_id.id,
                    "default_partner_id": self.equipment_id.partner_id.id,
                }

            if context:
                picking = self.env["stock.picking"].with_context(context)

                context["default_move_lines"] = []

                value = picking.move_lines.onchange_product_id(prod_id=self.equipment_id.product_id.id)["value"]
                value["location_id"] = picking.move_lines._default_location_source()
                value["location_dest_id"] = picking.move_lines._default_location_destination()
                value["date_expected"] = self.date
                value["product_id"] = self.equipment_id.product_id.id
                value["quant_ids"] = [(6, False, [self.equipment_id.quant_id.id])]
                context["default_move_lines"] += [(0, 0, value)]

                action = {
                    "name": _("Equipment Transfer"),
                    "view_type": "form",
                    "view_mode": "form",
                    "res_model": "stock.picking",
                    "view_id": False,
                    "views": [[False, "form"]],
                    "context": context,
                    "type": "ir.actions.act_window",
                }

        return action
