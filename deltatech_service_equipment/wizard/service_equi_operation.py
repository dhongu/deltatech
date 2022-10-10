# ©  2015-2021 Deltatech
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
        [("add", "Add to Agreement"), ("ins", "Installation"), ("rem", "Removal")],
        string="Operation",
        default="ins",
        readonly=True,
    )
    period_id = fields.Many2one("date.range", string="Period")

    equipment_id = fields.Many2one("service.equipment", string="Equipment", readonly=True)

    partner_id = fields.Many2one("res.partner", string="Customer", domain=[("is_company", "=", True)])
    address_id = fields.Many2one("res.partner", string="Location")  # sa fac un nou tip de partener? locatie ?
    emplacement = fields.Char(string="Emplacement")
    agreement_id = fields.Many2one("service.agreement", string="Contract Service")

    can_remove = fields.Boolean(compute="_compute_can_remove")

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
            agreement = self.env["service.agreement"].search([("partner_id", "=", equipment.partner_id.id)], limit=1)
            if agreement:
                defaults["agreement_id"] = agreement.id
        else:
            raise UserError(_("Please select equipment."))
        return defaults

    @api.onchange("partner_id")
    def onchange_partner_id(self):
        self.address_id = self.partner_id

    def _compute_can_remove(self):
        # ca sa se poata elimina dintr-un contract trebuie ca:
        # citirea introdusa sa fie egala cu ultima citire de pe contor
        # ultima citire trebuie sa fie facturata
        # sau echipamentul sa nu aiba linii cu contori
        can_remove = True
        # check if equipment has lines with meters
        agreement_lines = self.agreement_id.agreement_line.filtered(
            lambda l: l.equipment_id == self.equipment_id and l.meter_id
        )
        if agreement_lines:
            for reading in self.items:
                last_meter_reading_id = reading.meter_id.last_meter_reading_id
                # ultima citire trebuie sa fie egala cu citirea actuala
                if last_meter_reading_id.counter_value != reading.counter_value:
                    can_remove = False
                # ultima citire trebuie sa aiba consum generat
                if not last_meter_reading_id.consumption_id:
                    can_remove = False

        self.can_remove = can_remove

    def do_operation(self):
        counters = ""
        for reading in self.items:
            counters += str(reading.meter_id.uom_id.name) + ": " + str(reading.counter_value) + "\r\n"

        if self.state == "ins":
            emplacement = self.emplacement or ""
            message = _("Equipment installation at %s, address %s, emplacement %s.\r\rMeters: %s") % (
                self.partner_id.name,
                self.address_id.name,
                emplacement,
                counters,
            )

            values = {"name": _("Installation"), "equipment_id": self.equipment_id.id, "description": message}
            self.env["service.history"].create(values)

        if self.state in ["ins", "add"]:
            self.equipment_id.write(
                {
                    "partner_id": self.partner_id.id,
                    "address_id": self.address_id.id,
                    "emplacement": self.emplacement,
                    "state": "installed",
                    "installation_date": fields.Date.today(),
                }
            )

        for item in self.items:
            self.env["service.meter.reading"].create(
                {
                    "meter_id": item.meter_id.id,
                    "equipment_id": item.meter_id.equipment_id.id,
                    "date": self.date,
                    "read_by": self.read_by.id,
                    "note": self.note,
                    "counter_value": item.counter_value,
                }
            )

        if self.state == "rem":
            domain = [("equipment_id", "=", self.equipment_id.id)]
            agreement_lines = self.env["service.agreement.line"].search(domain)
            agreement_lines.with_context(from_uninstall=True).do_billing_preparation(self.period_id)
            self._compute_can_remove()

            if not self.can_remove:
                raise UserError(_("You must bill consumption before uninstalling"))
            emplacement = self.equipment_id.emplacement or ""
            message = _("Uninstalling equipment from %s, address %s, emplacement %s.\r\rMeters: %s") % (
                self.partner_id.name,
                self.address_id.name,
                emplacement,
                counters,
            )
            values = {"name": _("Uninstall"), "equipment_id": self.equipment_id.id, "description": message}
            self.env["service.history"].create(values)

            self.equipment_id.write(
                {
                    "partner_id": False,
                    "address_id": False,
                    "emplacement": False,
                    "agreement_id": False,
                    "state": "available",
                    "installation_date": False,
                }
            )

            agreement_lines.write({"active": False})

        action = True
        if self.state == "add":
            action = self.do_agreement()

        self.equipment_id.update_meter_status()
        return action

    def do_agreement(self):

        counters = ""
        if self.equipment_id.meter_ids:
            for meter in self.equipment_id.meter_ids:
                counters += str(meter.uom_id.name) + ": " + str(meter.total_counter_value) + "\r\n"
        emplacement = self.equipment_id.emplacement or ""
        message = _("Add to contract %s, partner %s, address %s, emplacement %s.") % (
            self.agreement_id.name,
            self.equipment_id.partner_id.name,
            self.equipment_id.address_id.name,
            emplacement,
        )
        message += "\r\n"
        message += _("Meters: %s") % counters
        values = {
            "name": _("Add to contract"),
            "equipment_id": self.equipment_id.id,
            "agreement_id": self.agreement_id.id,
            "description": message,
        }
        self.env["service.history"].create(values)

        if not self.agreement_id:
            cycle = self.env.ref("deltatech_service_agreement.cycle_monthly")
            values = {"partner_id": self.partner_id.id, "cycle_id": cycle.id, "state": "draft"}
            self.agreement_id = self.env["service.agreement"].create(values)

        # self.equipment_id.write({'agreement_id':self.agreement_id.id,
        #                         'partner_id':self.partner_id.id})
        for template in self.equipment_id.type_id.template_meter_ids:
            values = {
                "agreement_id": self.agreement_id.id,
                "equipment_id": self.equipment_id.id,
                "currency_id": template.currency_id.id,
                "product_id": template.product_id.id,
                # "analytic_account_id": template.analytic_account_id.id,
            }
            for meter in self.equipment_id.meter_ids:
                if meter.meter_categ_id == template.meter_categ_id:
                    values["meter_id"] = meter.id
                    values["uom_id"] = template.meter_categ_id.bill_uom_id.id

            self.env["service.agreement.line"].create(values)

        self.equipment_id.write({"agreement_id": self.agreement_id})

        action = {
            "domain": "[('id','=',%s)]" % self.agreement_id.id,
            "name": _("Service Agreement"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "service.agreement",
            "view_id": False,
            "type": "ir.actions.act_window",
            "res_id": self.agreement_id.id,
        }
        return action
