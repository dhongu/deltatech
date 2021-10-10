# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FleetServiceType(models.Model):
    _inherit = "fleet.service.type"

    category = fields.Selection(selection_add=[("fuel", "Fuel")], default="service", ondelete={"fuel": "set default"})


class FleetVehicleLogFuel(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _inherits = {"fleet.vehicle.log.services": "log_service_id"}
    _name = "fleet.vehicle.log.fuel"
    _description = "Vehicle Fuel Log"
    _order = "date desc"

    name = fields.Char()
    liter = fields.Float()
    price_per_liter = fields.Float()

    log_service_id = fields.Many2one("fleet.vehicle.log.services", ondelete="cascade")

    # comune cu: fleet.vehicle.log.services
    # amount = fields.Float(string="Amount", store=True, readonly=False)
    # vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicle")
    # odometer_id = fields.Many2one(
    #     "fleet.vehicle.odometer", "Odometer", help="Odometer measure of the vehicle at the moment of this log"
    # )
    # odometer = fields.Float(
    #     compute="_compute_odometer",
    #     inverse="_inverse_odometer",
    #     string="Odometer Value",
    #     help="Odometer measure of the vehicle at the moment of this log",
    # )
    # odometer_unit = fields.Selection(related="vehicle_id.odometer_unit", string="Unit", readonly=True)
    # date = fields.Datetime(help="Date when the cost has been executed")  # de ce nu e Date?
    # state = fields.Selection(
    #     [("draft", "Draft"), ("done", "Done")],
    #     string="Status",
    #     readonly=True,
    #     help="When the Log Fuel is created the status is set to 'Draft'.\n\
    #                                   When the Log Fuel is closed, the status is set to 'Done'.",
    # )
    # notes = fields.Text()
    #
    # service_type_id = fields.Many2one(
    #     'fleet.service.type', 'Service Type', required=True,
    #     default=lambda self: self.env.ref('deltatech_fleet.type_service_service_fuel', raise_if_not_found=False),
    # )

    map_sheet_id = fields.Many2one(
        "fleet.map.sheet",
        string="Map Sheet",
        domain="['&',('vehicle_id','=',vehicle_id),('date_start','<=',date_time),('date_end','>=',date_time)]",
    )
    fuel_id = fields.Many2one("fleet.fuel", string="Fuel")
    card_id = fields.Many2one("fleet.card", string="Card")
    full = fields.Boolean(string="To full", help="Fuel supply was made up to full")
    reservoir_level = fields.Float(compute="_compute_reservoir_level", string="Level Reservoir", store=False)
    date_time = fields.Datetime(help="Date when the cost has been executed")

    @api.onchange("liter", "price_per_liter", "amount")
    def _onchange_liter_price_amount(self):
        # need to cast in float because the value receveid from web client maybe an integer (Javascript and JSON do not
        # make any difference between 3.0 and 3). This cause a problem if you encode, for example, 2 liters at 1.5 per
        # liter => total is computed as 3.0, then trigger an onchange that recomputes price_per_liter as 3/2=1 (instead
        # of 3.0/2=1.5)
        # If there is no change in the result, we return an empty dict to prevent an infinite loop due to the 3 intertwine
        # onchange. And in order to verify that there is no change in the result, we have to limit the precision of the
        # computation to 2 decimal
        liter = float(self.liter)
        price_per_liter = float(self.price_per_liter)
        amount = float(self.amount)
        if liter > 0 and price_per_liter > 0 and round(liter * price_per_liter, 2) != amount:
            self.amount = round(liter * price_per_liter, 2)
        elif amount > 0 and liter > 0 and round(amount / liter, 2) != price_per_liter:
            self.price_per_liter = round(amount / liter, 2)
        elif amount > 0 and price_per_liter > 0 and round(amount / price_per_liter, 2) != liter:
            self.liter = round(amount / price_per_liter, 2)

    @api.depends("vehicle_id", "date_time")
    def _compute_reservoir_level(self):
        for item in self:
            if item.vehicle_id and item.date_time:
                item.reservoir_level = self.env["fleet.reservoir.level"].get_level_to(item.vehicle_id, item.date_time)
            else:
                item.reservoir_level = 0

    @api.onchange("vehicle_id")
    def _onchange_vehicle(self):
        self.map_sheet_id = False

    def _compute_odometer(self):
        self.odometer = 0
        for record in self:
            if record.odometer_id:
                record.odometer = record.odometer_id.value

    def _inverse_odometer(self):
        for record in self:
            if not record.odometer:
                raise UserError(_("Emptying the odometer value of a vehicle is not allowed."))
            odometer = self.env["fleet.vehicle.odometer"].create(
                {
                    "value": record.odometer,
                    "date": record.date or fields.Date.context_today(record),
                    "vehicle_id": record.vehicle_id.id,
                }
            )
            self.odometer_id = odometer
