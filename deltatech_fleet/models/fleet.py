# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models

# class FleetVehicleCost(models.Model):
#     _inherit = "fleet.vehicle.cost"
#
#     date_time = fields.Datetime(string="Date Time", help="Date and time when the cost has been executed")
#     # modific campul din data in datatimp ?
#     # date = fields.Date(string='Date', help='Date and time when the cost has been executed',
#     # compute='_compute_get_date', inverse='_compute_set_date', store=True)
#     year = fields.Char(string="Year", store=True, compute="_compute_year")
#
#     @api.depends("date")
#     def _compute_year(self):
#         for cost in self:
#             if cost.date:
#                 cost.year = str(fields.Date.from_string(cost.date).year)
#
#     def write(self, vals):
#         if "date_time" in vals and "date" not in vals:
#             vals["date"] = vals["date_time"]
#         if "date" in vals and "date_time" not in vals:
#             vals["date_time"] = vals["date"]
#         res = super(FleetVehicleCost, self).write(vals)
#         return res


class FleetVehicleOdometer(models.Model):
    _inherit = "fleet.vehicle.odometer"

    date_time = fields.Datetime(string="Date Time", default=fields.Datetime.now)
    real = fields.Boolean(string="Is real")

    def write(self, vals):
        if "date_time" in vals and "date" not in vals:
            vals["date"] = vals["date_time"]
        if "date" in vals and "date_time" not in vals:
            vals["date_time"] = vals["date"]
        res = super(FleetVehicleOdometer, self).write(vals)
        return res


class FleetRoute(models.Model):
    _name = "fleet.route"
    _description = "Route"

    name = fields.Char(string="Name", store=False, compute="_compute_name")
    from_loc_id = fields.Many2one("fleet.location", string="From", help="From location", required=True)
    to_loc_id = fields.Many2one("fleet.location", string="To", help="To location", required=True)
    distance = fields.Float("Distance")
    duration = fields.Float("Duration")
    dist_c1 = fields.Float("Dist C1")
    dist_c2 = fields.Float("Dist C2")
    dist_c3 = fields.Float("Dist C3")
    reverse = fields.Many2one("fleet.route", string="Reverse route")

    @api.depends("from_loc_id.name", "to_loc_id.name")
    def _compute_name(self):
        for route in self:
            route.name = route.from_loc_id.name + "-" + route.to_loc_id.name

    def button_create_reverse(self):
        for route in self:
            if not route.reverse:
                new_route = route.copy(
                    {"from_loc_id": route.to_loc_id.id, "to_loc_id": route.from_loc_id.id, "reverse": route.id}
                )
                route.reverse = new_route


class FleetCard(models.Model):
    _name = "fleet.card"
    _description = "Fuel Card"

    name = fields.Char(string="Series card", size=20, required=True)
    type_card = fields.Selection(
        [("2", "Own pomp"), ("3", "Rompetrol"), ("4", "Petrom"), ("5", "Lukoil"), ("6", "OMV")], string="Type Card"
    )
    vehicle_ids = fields.Many2many(
        "fleet.vehicle", "fleet_card_vehicle_rel", "card_id", "vehicle_id", string="Vehicles"
    )
    log_fuel_ids = fields.One2many("fleet.vehicle.log.fuel", "card_id", string="Fuel log")
    active = fields.Boolean(string="Active", default=1)

    _sql_constraints = [("serie_uniq", "unique (name)", "The series must be unique !")]


class FleetFuel(models.Model):
    _name = "fleet.fuel"
    _description = "Fuel"

    name = fields.Char(string="Fuel", size=75, required=True)
    fuel_type = fields.Selection([("gasoline", "Gasoline"), ("diesel", "Diesel")], string="Fuel Type")


class FleetScope(models.Model):
    _name = "fleet.scope"
    _description = "Scope"

    name = fields.Char(string="Scope", size=75, required=True)
    categ_id = fields.Many2one("fleet.scope.categ", string="Category")


class FleetScopeCateg(models.Model):
    _name = "fleet.scope.categ"
    _description = "Scope"

    name = fields.Char(string="Category", required=True)


class FleetDivision(models.Model):
    _name = "fleet.division"
    _description = "Division"

    name = fields.Char(string="Division", required=True)


class FleetLocation(models.Model):
    " Pozitia unei locatii si afisare pozitie pe Google Maps "
    _name = "fleet.location"
    _description = "Location"

    name = fields.Char(string="Location", size=100, required=True)
    type = fields.Selection([("0", "Other"), ("1", "Partner"), ("2", "Station")], default="0", string="Type")


class FleetVehicleCategory(models.Model):
    _name = "fleet.vehicle.category"
    _description = "Vehicle Category"

    name = fields.Char(string="Category", size=100, required=True)
    code = fields.Char(string="Cod", size=4, required=True)


class FleetReservoirLevel(models.Model):
    _name = "fleet.reservoir.level"
    _description = "Fleet Reservoir Level"

    date = fields.Date(string="Date", required=True)
    vehicle_id = fields.Many2one("fleet.vehicle", string="Vehicle", required=True)
    liter = fields.Float("Liter")

    @api.model
    def get_level(self, vehicle_id):
        level = 0.0
        if not vehicle_id:
            return level

        self.env.cr.execute(
            """SELECT  sum(liter) AS liter
              FROM fleet_vehicle_log_fuel
                   JOIN fleet_vehicle_log_services as sl on sl.id = log_service_id
              WHERE sl.vehicle_id = %s
           """,
            (vehicle_id,),
        )
        results = self.env.cr.dictfetchone()
        if results:
            level = results["liter"]
            if level is None:
                level = 0
        self.env.cr.execute(
            """SELECT  sum(norm_cons) AS liter
              FROM fleet_route_log
              WHERE vehicle_id = %s
           """,
            (vehicle_id,),
        )
        results = self.env.cr.dictfetchone()
        if results and results["liter"]:
            level = level - results["liter"]

        return level

    @api.model
    def get_level_to(self, vehicle, to_date):
        level = 0.0
        if not vehicle:
            return level

        vehicle_id = vehicle.id
        self.env.cr.execute(
            """SELECT  sum(liter) AS liter
              FROM fleet_vehicle_log_fuel
              JOIN fleet_vehicle_log_services as sl on sl.id = log_service_id
              WHERE sl.vehicle_id = %s and
                   date_time <= %s
           """,
            (
                vehicle_id,
                to_date,
            ),
        )
        results = self.env.cr.dictfetchone()
        if results and results["liter"]:
            level = results["liter"]
            if level is None:
                level = 0
        self.env.cr.execute(
            """SELECT  sum(norm_cons) AS liter
              FROM fleet_route_log
              WHERE vehicle_id = %s  and
                   date_end <= %s
           """,
            (
                vehicle_id,
                to_date,
            ),
        )
        results = self.env.cr.dictfetchone()
        if results and results["liter"]:
            level = level - results["liter"]

        return level
