# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import datetime

import pytz

from odoo import api, fields, models


class FleetVehicleLocation(models.Model):
    _name = "fleet.vehicle.location"
    _description = "vehicle Location"

    vehicle_id = fields.Many2one("fleet.vehicle")
    date = fields.Datetime()
    name = fields.Char(string="Address")


class FleetVehicle(models.Model):
    _inherit = "fleet.vehicle"

    # name = fields.Char(compute='_compute_vehicle_name', string="Name", store=True)
    indicative = fields.Char(string="Indicative", size=32)
    driver2_id = fields.Many2one("res.partner", string="Backup Driver", help="Backup driver of the vehicle")
    mass_cap = fields.Float(string="Mass capacity")
    weight = fields.Float(string="Useful weight")
    tachometer = fields.Boolean(string="Tachometer", help="Status of tachometer")
    reservoir = fields.Float(string="Reservoir capacity")
    reservoir_level = fields.Float(compute="_compute_reservoir_level", string="Level Reservoir", store=False)
    loading_level = fields.Float(string="Level of loading")

    card_ids = fields.Many2many("fleet.card", "fleet_card_vehicle_rel", "vehicle_id", "card_id", string="Cards")
    avg_cons = fields.Float(string="Average Consumption", default=8.0)
    avg_cons_ex = fields.Float(string="Average Consumption Exterior", default=7.0)
    avg_cons_in = fields.Float(string="Average Consumption Urban", default=9.0)
    avg_speed = fields.Float(string="Average Speed", default=70.0)
    category_id = fields.Many2one("fleet.vehicle.category", string="Vehicle Category")

    engine_sn = fields.Char("Engine Serial Number", copy=False)

    # usage_mod = fields.Selection([()])
    allocation_mode = fields.Char("Allocation mode")
    ownership_partner_id = fields.Many2one(
        "res.partner", string="Ownership Company", domain=[("is_company", "=", True)]
    )
    contract_partner_id = fields.Many2one(
        "res.partner", string="Contract Owner Company", domain=[("is_company", "=", True)]
    )
    utilized_partner_id = fields.Many2one(
        "res.partner", string="Utilized by company", domain=[("is_company", "=", True)]
    )

    division = fields.Many2one("fleet.division")
    scope_id = fields.Many2one("fleet.scope", string="Scope")

    _sql_constraints = [("indicative_uniq", "unique (indicative)", "The Indicative must be unique !")]

    def act_show_map_sheet(self):
        """This opens map sheet view to view and add new map sheet for this vehicle
        @return: the map sheet view
        """
        self.ensure_one()
        result = self.env.ref("deltatech_fleet.fleet_map_sheet_act").sudo().read()[0]
        result["context"] = dict(self.env.context, default_vehicle_id=self.id)
        result["domain"] = [("vehicle_id", "=", self.id)]
        return result

    def _compute_reservoir_level(self):
        for vehicle in self:
            if not isinstance(vehicle.id, models.NewId):
                vehicle.reservoir_level = self.env["fleet.reservoir.level"].get_level(vehicle.id)
            else:
                vehicle.reservoir_level = 0

    @api.model
    def _conv_local_datetime_to_utc(self, date):
        tz_name = self.env.context["tz"]
        local = pytz.timezone(tz_name)
        if isinstance(date, str):
            naive = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        else:
            naive = date
        if naive.tzinfo is None:
            local_dt = local.localize(naive, is_dst=None)
        else:
            local_dt = naive
        utc_dt = local_dt.astimezone(pytz.utc)
        return utc_dt.strftime("%Y-%m-%d %H:%M:%S")
