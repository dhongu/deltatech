# ©  2015-2021 Deltatech
# See README.rst file on addons root folder for license details


from datetime import date

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ServiceEquipment(models.Model):
    _inherit = "service.equipment"

    _inherits = {"maintenance.equipment": "base_equipment_id"}

    base_equipment_id = fields.Many2one("maintenance.equipment", required=True, ondelete="cascade")

    state = fields.Selection(
        [
            ("available", "Available"),
            ("installing", "In installing"),
            ("installed", "Installed"),
            ("inactive", "Inactive"),
            ("backuped", "Backuped"),
        ],
        default="available",
        string="Status",
        copy=False,
    )

    agreement_id = fields.Many2one("service.agreement", string="Contract Service")
    agreement_type_id = fields.Many2one(
        "service.agreement.type", string="Agreement Type", related="agreement_id.type_id"
    )
    agreement_state = fields.Selection(string="Status contract", store=True, related="agreement_id.state")

    # se gaseste in echipmanet campul technician_user_id
    # user_id = fields.Many2one('res.users', string='Responsible', tracking=True)

    partner_id = fields.Many2one("res.partner", string="Customer", readonly=True)

    address_id = fields.Many2one(
        "res.partner",
        string="Address",
        readonly=True,
        help="The address where the equipment is located",
    )

    location_state_id = fields.Many2one(
        "res.country.state",
        string="Region",
        related="address_id.state_id",
        store=True,
    )
    emplacement = fields.Char(
        string="Emplacement",
        readonly=True,
        help="Detail of location of the equipment in working point",
    )

    # install_date = fields.Date(string='Installation Date',  readonly=True)

    # se va calcula din suma consumurilor de servicii

    total_invoiced = fields.Float(string="Total invoiced", readonly=True)
    total_revenues = fields.Float(string="Total Revenues", readonly=True)
    # se va calcula din suma avizelor
    total_costs = fields.Float(string="Total cost", readonly=True)

    start_date = fields.Date(string="Start Date")

    meter_ids = fields.One2many("service.meter", "equipment_id", string="Meters", copy=True)

    readings_status = fields.Selection(
        [("", "N/A"), ("unmade", "Unmade"), ("done", "Done")],
        string="Readings Status",
        compute="_compute_readings_status",
        default="unmade",
        store=True,
    )

    group_id = fields.Many2one("service.agreement.group", string="Service Group")
    internal_type = fields.Selection([("equipment", "Equipment")], default="equipment")

    analytic_account_id = fields.Many2one("account.analytic.account", string="Analytic", ondelete="restrict")

    location_id = fields.Many2one(
        "stock.location", "Stock Location", store=True, compute="_compute_location"
    )  # related='quant_id.location_id'

    ean_code = fields.Char(string="EAN Code")

    common_history_ids = fields.One2many("service.history", "equipment_id", string="Equipment History")

    location_type = fields.Selection(
        [
            ("stock", "In Stock"),
            ("rental", "In rental"),  # green  success
            ("customer", "Customer"),  # blue  info
            ("unavailable", "Unavailable"),  # red  danger
        ],
        default="stock",
        store=True,
        compute="_compute_location_type",
    )

    reading_day = fields.Integer(
        string="Reading Day",
        default=-1,
        help="""Day of the month, set -1 for the last day of the month.
                                     If it's positive, it gives the day of the month. Set 0 for net days .""",
    )
    last_reading = fields.Date("Last Reading Date", readonly=True, default="2000-01-01")
    next_reading = fields.Date("Next reading date", readonly=True, default="2000-01-01")
    last_reading_value = fields.Float(string="Last reading value")
    installation_date = fields.Date("Installation Date")

    _sql_constraints = [
        ("ean_code_uniq", "unique(ean_code)", "EAN Code already exist!"),
    ]

    @api.depends("serial_id.quant_ids")
    def _compute_location(self):
        for equipment in self:
            if not equipment.serial_id:  # multiple quants, can be in different locations
                equipment.location_id = False
            else:
                quants = equipment.serial_id.quant_ids.filtered(lambda x: x.quantity > 0)
                if len(quants) == 1:
                    equipment.location_id = quants.location_id
                else:
                    equipment.location_id = False

    def compute_totals(self):
        for equipment in self:
            total_consumption = 0.0
            total_invoiced = 0.0
            consumptions = self.env["service.consumption"].search([("equipment_id", "=", equipment.id)])
            invoices = self.env["account.move"]
            for consumption in consumptions:
                if consumption.state == "done":
                    total_consumption += consumption.revenues
                    invoices |= consumption.invoice_id
            for invoice in invoices:
                if invoice.state == "posted":
                    for line in invoice.invoice_line_ids:
                        if line.agreement_line_id.equipment_id == equipment:
                            total_invoiced += line.price_subtotal
            equipment.write({"total_invoiced": total_invoiced, "total_revenues": total_consumption})

    def costs_and_revenues(self):
        self.compute_totals()

    @api.depends("location_id")
    def _compute_location_type(self):
        for equipment in self:

            if equipment.location_id.usage == "customer":
                equipment.location_type = "customer"
            elif equipment.location_id.usage == "internal":
                equipment.location_type = "stock"
            else:
                equipment.location_type = "unavailable"

            if equipment.location_id.rental:
                equipment.location_type = "rental"

    def _compute_readings_status(self):
        for equi in self:
            if equi.last_reading:
                next_date = max(date.today(), equi.last_reading)
            else:
                next_date = date.today()

            if equi.reading_day < 0:
                next_first_date = next_date + relativedelta(day=1, months=0)
                next_date = next_first_date + relativedelta(days=equi.reading_day)
            if equi.reading_day > 0:
                next_date += relativedelta(day=equi.reading_day, months=0)

            next_reading_date = next_date

            equi.readings_status = "done"
            for meter in equi.meter_ids:
                if not meter.last_meter_reading_id:
                    equi.readings_status = "unmade"
                    break
                else:
                    equi.last_reading = meter.last_meter_reading_id.date
                if not (meter.last_meter_reading_id.date >= next_reading_date):
                    equi.readings_status = "unmade"
                    break

            if next_reading_date < equi.last_reading:
                next_date += relativedelta(months=1)
            equi.next_reading = next_date

    # def _compute_readings_status(self):
    #     from_date = date.today() + relativedelta(day=1, months=0, days=0)
    #     to_date = date.today() + relativedelta(day=1, months=1, days=-1)
    #     from_date = fields.Date.to_string(from_date)
    #     to_date = fields.Date.to_string(to_date)
    #
    #     for equi in self:
    #         equi.readings_status = "done"
    #         for meter in equi.meter_ids:
    #             if not meter.last_meter_reading_id:
    #                 equi.readings_status = "unmade"
    #                 break
    #             if not (from_date <= meter.last_meter_reading_id.date <= to_date):
    #                 equi.readings_status = "unmade"
    #                 break
    #             else:
    #                 equi.last_reading

    def invoice_button(self):
        consumptions = self.env["service.consumption"].search([("equipment_id", "=", self.id)])

        invoices = self.env["account.move"]
        for consumption in consumptions:
            if consumption.state == "done":
                invoices |= consumption.invoice_id

        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_service_agreement.action_service_invoice")
        action["domain"] = [("id", "=", invoices.ids)]
        return action

    def create_meters_button(self):
        categs = self.env["service.meter.category"]
        for equi in self:
            for template in equi.type_id.template_meter_ids:
                categs |= template.meter_categ_id
            for categ in categs:
                equi.meter_ids.create({"equipment_id": equi.id, "meter_categ_id": categ.id, "uom_id": categ.uom_id.id})

    def update_meter_status(self):
        self._compute_readings_status()

    # o fi ok sa elimin echipmanetul din contract
    def remove_from_agreement_button(self):
        self.ensure_one()
        if self.agreement_id.state == "draft":
            lines = self.env["service.agreement.line"].search(
                [("agreement_id", "=", self.agreement_id.id), ("equipment_id", "=", self.id)]
            )
            # lines.unlink()
            # if not self.agreement_id.agreement_line:
            #     self.agreement_id.unlink()
            lines.write({"active": False, "quantity": 0})
            self.agreement_id = False
        else:
            raise UserError(_("The agreement %s is in state %s") % (self.agreement_id.name, self.agreement_id.state))

    def do_agreement(self):
        pass

    def common_history_button(self):
        return {
            "domain": [("id", "in", self.common_history_ids.ids)],
            "name": "History",
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "service.history",
            "view_id": False,
            "type": "ir.actions.act_window",
        }

    @api.model
    def name_search(self, name="", args=None, operator="ilike", limit=100):
        res_serial = []
        if name and len(name) > 3:
            equipment_ids = self.search(["|", ("serial_id", "ilike", name), ("ean_code", "ilike", name)], limit=10)
            if equipment_ids:
                res_serial = equipment_ids.name_get()
        res = super(ServiceEquipment, self).name_search(name, args, operator=operator, limit=limit) + res_serial
        return res

    def name_get(self):
        res = []
        for equipment in self:
            name = equipment.name
            if equipment.address_id:
                name += "/" + equipment.address_id.name
            if equipment.serial_id:
                name += "/" + equipment.serial_id.name
            res.append((equipment.id, name))
        return res


# se va utiliza maintenance.equipment.category
class ServiceEquipmentCategory(models.Model):
    _inherit = "maintenance.equipment.category"

    template_meter_ids = fields.One2many("service.template.meter", "categ_id")


class ServiceEquipmentType(models.Model):
    _inherit = "service.equipment.type"

    categ_id = fields.Many2one("maintenance.equipment.category", string="Category")

    template_meter_ids = fields.One2many("service.template.meter", related="categ_id.template_meter_ids")

    @api.depends("categ_id")
    def _compute_template_meter_ids(self):
        for equipment_type in self:
            equipment_type.template_meter_ids = equipment_type.categ_id.template_meter_ids


# este utilizat pentru generare de pozitii noi in contract si pentru adugare contori noi
class ServiceTemplateMeter(models.Model):
    _name = "service.template.meter"
    _description = "Service Template Meter"

    categ_id = fields.Many2one("maintenance.equipment.category", string="Category")
    type_id = fields.Many2one("service.equipment.type", string="Type")
    product_id = fields.Many2one(
        "product.product", string="Service", ondelete="set null", domain=[("type", "=", "service")]
    )
    meter_categ_id = fields.Many2one("service.meter.category", string="Meter category")
    bill_uom_id = fields.Many2one("uom.uom", string="Billing Unit of Measure")
    currency_id = fields.Many2one(
        "res.currency", string="Currency", required=True, domain=[("name", "in", ["RON", "EUR"])]
    )
    company_id = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)

    @api.onchange("meter_categ_id")
    def onchange_meter_categ_id(self):
        self.bill_uom_id = self.meter_categ_id.bill_uom_id
