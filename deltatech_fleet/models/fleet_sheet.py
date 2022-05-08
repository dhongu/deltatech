# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import math
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class FleetMapSheet(models.Model):
    _inherit = "mail.thread"
    _name = "fleet.map.sheet"
    _description = "Fleet Map Sheet"

    @api.depends("vehicle_id", "date_start", "distance_total")
    def _compute_odometer_start(self):

        for record in self:
            if record.odometer_start_id:
                record.odometer_start = record.odometer_start_id.value
            else:
                odometer = self.env["fleet.vehicle.odometer"].search(
                    [("vehicle_id", "=", record.vehicle_id.id), ("date", "<=", record.date_start)],
                    limit=1,
                    order="date desc",
                )
                if odometer:
                    record.odometer_start = odometer.value
                    if not record.odometer_end_id:
                        record.odometer_end = record.odometer_start + record.distance_total
                else:
                    if record.odometer_end_id:
                        record.odometer_start = record.odometer_end_id.value - record.distance_total
                    else:
                        record.odometer_start = 0

    @api.depends("vehicle_id", "date_end", "distance_total")
    def _compute_odometer_end(self):

        for record in self:
            if record.odometer_end_id:
                record.odometer_end = record.odometer_end_id.value
            else:
                odometer = self.env["fleet.vehicle.odometer"].search(
                    [("vehicle_id", "=", record.vehicle_id.id), ("date", ">=", record.date_end)], limit=1, order="date"
                )
                if odometer:
                    record.odometer_end = odometer.value
                else:
                    if record.odometer_start_id:
                        record.odometer_end = record.odometer_start_id.value + record.distance_total
                    else:
                        record.odometer_end = record.odometer_start + record.distance_total

    def _inverse_odometer_start(self):
        for sheet in self:
            if sheet.odometer_start:
                data = {"value": sheet.odometer_start, "date": sheet.date_start, "vehicle_id": sheet.vehicle_id.id}
                if sheet.odometer_start_id:
                    sheet.odometer_start_id.write(data)
                else:
                    sheet.odometer_start_id = self.env["fleet.vehicle.odometer"].create(data)

    def _inverse_odometer_end(self):
        for sheet in self:
            if sheet.odometer_end:
                data = {"value": sheet.odometer_end, "date": sheet.date_end, "vehicle_id": sheet.vehicle_id.id}
                if sheet.odometer_end_id:
                    sheet.odometer_end_id.write(data)
                else:
                    sheet.odometer_end_id = self.env["fleet.vehicle.odometer"].create(data)

    @api.depends("route_log_ids", "log_fuel_ids")
    def _compute_amount_all(self):
        for sheet in self:
            liter = amount = 0.0
            distance_total = 0.0
            norm_cons = 0.0
            for log_fuel in sheet.log_fuel_ids:
                liter += log_fuel.liter
                amount += log_fuel.amount
            sheet.liter_total = liter
            sheet.amount_total = amount

            for route in sheet.route_log_ids:
                distance_total += route.distance
                norm_cons += route.norm_cons
            sheet.distance_total = distance_total
            sheet.norm_cons = norm_cons

    @api.depends("vehicle_id", "date_start")
    def _compute_reservoir_level_start(self):
        for sheet in self:
            sheet.reservoir_level_start = self.env["fleet.reservoir.level"].get_level_to(
                sheet.vehicle_id, sheet.date_start
            )

    @api.depends("vehicle_id", "date_end")
    def _compute_reservoir_level_end(self):
        for sheet in self:
            sheet.reservoir_level_end = self.env["fleet.reservoir.level"].get_level_to(sheet.vehicle_id, sheet.date_end)

    @api.model
    def _get_default_date_start(self):
        context = self.env.context
        if context and "date" in context:
            res = self.vehicle_id._conv_local_datetime_to_utc(context["date"][:10] + " 00:00:00")
        else:
            res = fields.Datetime.now()
        return res

    @api.model
    def _get_default_date_end(self):
        context = self.env.context
        if context and "date" in context:
            res = self.vehicle_id._conv_local_datetime_to_utc(context["date"][:10] + " 23:59:59")
        else:
            res = fields.Datetime.now()
        return res

    @api.model
    def _get_default_date(self):
        context = self.env.context
        if context and "date" in context:
            res = context["date"]
        else:
            res = fields.Date.today()
        return res

    name = fields.Char(
        string="Number",
        size=20,
        required=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        default=lambda self: self.env["ir.sequence"].next_by_code("fleet.map.sheet") or "/",
    )

    date = fields.Date(
        string="Date", required=True, readonly=True, states={"draft": [("readonly", False)]}, default=_get_default_date
    )
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        required=True,
        help="Vehicle",
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    category_id = fields.Many2one(
        "fleet.vehicle.category", related="vehicle_id.category_id", readonly=True, string="Vehicle Category"
    )
    driver_id = fields.Many2one(
        "res.partner", string="Driver", help="Driver of the vehicle", states={"done": [("readonly", True)]}
    )
    driver2_id = fields.Many2one(
        "res.partner",
        string="Backup Driver",
        help="Backup driver of the vehicle",
        states={"done": [("readonly", True)]},
    )
    avg_cons = fields.Float(related="vehicle_id.avg_cons", readonly=True, string="Average Consumption")

    date_start = fields.Datetime(
        string="Date Start",
        help="Date time at the start of this map sheet",
        states={"done": [("readonly", True)]},
        default=_get_default_date_start,
    )
    date_start_old = fields.Datetime(string="Old Date Start")  # Camp tehnic
    date_end = fields.Datetime(
        string="Date End",
        help="Date time at the end of this map sheet",
        states={"done": [("readonly", True)]},
        default=_get_default_date_end,
    )

    odometer_end = fields.Float(
        compute="_compute_odometer_end",
        inverse="_inverse_odometer_end",
        states={"done": [("readonly", True)]},
        string="Odometer End",
        help="Odometer measure of the vehicle at the end of this map sheet",
    )

    odometer_start = fields.Float(
        compute="_compute_odometer_start",
        inverse="_inverse_odometer_start",
        states={"done": [("readonly", True)]},
        string="Odometer Start",
        help="Odometer measure of the vehicle at the start of this map sheet",
    )

    odometer_start_id = fields.Many2one(
        "fleet.vehicle.odometer",
        string="ID Odometer start",
        domain="[('vehicle_id','=',vehicle_id)]",
        states={"done": [("readonly", True)]},
    )

    odometer_end_id = fields.Many2one(
        "fleet.vehicle.odometer",
        string="ID Odometer end",
        domain="[('vehicle_id','=',vehicle_id)]",
        states={"done": [("readonly", True)]},
    )

    state = fields.Selection(
        [("draft", "Draft"), ("open", "In Progress"), ("done", "Done"), ("cancel", "Cancelled")],
        string="Status",
        readonly=True,
        default="draft",
        help="When the Map Sheet is created the status is set to 'Draft'.\n\
                                      When the Map Sheet is in progress the status is set to 'In Progress' .\n\
                                      When the Map Sheet is closed, the status is set to 'Done'.",
    )

    log_fuel_ids = fields.One2many(
        "fleet.vehicle.log.fuel", "map_sheet_id", string="Fuel log", states={"done": [("readonly", True)]}, copy=False
    )
    route_log_ids = fields.One2many(
        "fleet.route.log", "map_sheet_id", string="Route Logs", states={"done": [("readonly", True)]}
    )

    liter_total = fields.Float(compute="_compute_amount_all", string="Total Liter", store=True, help="The total liters")

    amount_total = fields.Float(
        compute="_compute_amount_all", string="Total Amount", store=True, help="The total amount for fuel"
    )

    distance_total = fields.Float(
        compute="_compute_amount_all", string="Total distance", store=True, help="The total distance"
    )

    norm_cons = fields.Float(
        compute="_compute_amount_all", string="Normal Consumption", store=True, help="The Normal Consumption"
    )

    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company, required=True)

    reservoir_level_start = fields.Float(
        compute="_compute_reservoir_level_start",
        string="Level Reservoir Start",
        store=False,
        help="Fuel level in the reservoir at the beginning of road map",
    )
    reservoir_level_end = fields.Float(
        compute="_compute_reservoir_level_end",
        string="Level Reservoir End",
        store=False,
        help="Fuel level in the reservoir at the beginning of road map",
    )

    def action_read_odometer_start(self):
        self._compute_odometer_start()

    def action_read_odometer_end(self):
        self._compute_odometer_end()

    @api.constrains("date_start", "date_end")
    def _check_dates(self):
        for sheet in self:
            if sheet.date_start > sheet.date_end:
                raise ValidationError(
                    _("Map Sheet end-date (%s) must be greater then start-date (%s)")
                    % (sheet.date_end, sheet.date_start)
                )

    # @api.model
    # def _conv_local_datetime_to_utc(self, date):
    #     tz_name = self.env.context["tz"]
    #     local = pytz.timezone(tz_name)
    #     naive = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
    #     local_dt = local.localize(naive, is_dst=None)
    #     utc_dt = local_dt.astimezone(pytz.utc)
    #     return utc_dt.strftime("%Y-%m-%d %H:%M:%S")

    def copy(self, default=None):
        if not default:
            default = {}

        record = self

        date_start = fields.Datetime.from_string(record.date_start) + timedelta(days=1)
        date_start = fields.Datetime.to_string(date_start)

        date_end = fields.Datetime.from_string(record.date_end) + timedelta(days=1)
        date_end = fields.Datetime.to_string(date_end)

        date = fields.Date.from_string(record.date) + timedelta(days=1)
        date = fields.Date.to_string(date)

        # TODO: de introdus pozitii si pentru rute cu data incrementata
        default.update(
            {
                "log_fuel_ids": [],
                "name": self.env["ir.sequence"].next_by_code("fleet.map.sheet"),
                "date": date,
                "date_start": date_start,
                "date_end": date_end,
            }
        )
        new_id = super(FleetMapSheet, self).copy(default)
        return new_id

    @api.onchange("vehicle_id")
    def on_change_vehicle(self):
        if self.vehicle_id:
            self.driver_id = self.vehicle_id.driver_id.id
            self.driver2_id = self.vehicle_id.driver2_id.id

    @api.onchange("date_start", "date_end")
    def on_change_date_start(self):
        if not self.date_start_old:
            self.date_start_old = self.date_start

        new_date_start_int = fields.Datetime.from_string(self.date_start)
        old_date_start_int = fields.Datetime.from_string(self.date_start_old)
        date_dif = new_date_start_int - old_date_start_int

        # new_date_end_int = fields.Datetime.from_string(self.date_end)
        # date_end = fields.Datetime.to_string(new_date_end_int + date_dif)
        for route_log in self.route_log_ids:
            if route_log.state == "done":
                continue
            date_begin_int = fields.Datetime.from_string(route_log.date_begin)
            date_end_int = fields.Datetime.from_string(route_log.date_end)
            route_log.date_begin = fields.Datetime.to_string(date_begin_int + date_dif)
            route_log.date_end = fields.Datetime.to_string(date_end_int + date_dif)

    @api.onchange("route_log_ids")
    def on_change_route_log(self):
        if not self.route_log_ids:
            return {}

        new_date_start = self.date_start
        new_date_end = self.date_end

        for route_log in self.route_log_ids:

            if route_log.date_end > new_date_end:
                new_date_end = route_log.date_end

            if route_log.date_begin < new_date_start:
                new_date_start = route_log.date_begin

        # self.date_start = new_date_start
        self.date_end = new_date_end

    def write(self, vals):

        for map_sheet in self:
            map_sheet.log_fuel_ids.write({"vehicle_id": map_sheet.vehicle_id.id})
            map_sheet.route_log_ids.write({"vehicle_id": map_sheet.vehicle_id.id})
            if map_sheet.odometer_start_id:
                map_sheet.odometer_start_id.write({"vehicle_id": map_sheet.vehicle_id.id})
            if map_sheet.odometer_end_id:
                map_sheet.odometer_end_id.write({"vehicle_id": map_sheet.vehicle_id.id})

        res = super(FleetMapSheet, self).write(vals)
        return res

    # def unlink(self):
    #     """Allows to delete map sheet in draft,cancel states"""
    #     for rec in self:
    #         if rec.state not in ["draft", "cancel"]:
    #             raise UserError(_("Cannot delete a map sheet which is in state '%s'.") % (rec.state,))
    #     return super(FleetMapSheet, self).unlink()

    def button_dummy(self):
        return True

    def action_get_log_fuel(self):

        for record in self:
            fuel_log_ids = self.env["fleet.vehicle.log.fuel"].search(
                [
                    ("vehicle_id", "=", record.vehicle_id.id),
                    ("date_time", ">=", record.date_start),
                    ("date_time", "<=", record.date_end),
                    ("map_sheet_id", "=", None),
                ]
            )
            if fuel_log_ids:
                fuel_log_ids.write({"map_sheet_id": record.id})
        return True

    def action_get_route_log(self):

        for record in self:
            domain = [
                ("vehicle_id", "=", record.vehicle_id.id),
                ("date_begin", ">=", record.date_start),
                ("date_end", "<=", record.date_end),
                ("map_sheet_id", "=", None),
            ]
            log_route_ids = self.env["fleet.route.log"].search(domain)

            if log_route_ids:
                log_route_ids.write({"map_sheet_id": record.id})
        return True

    def action_open(self):
        self.write({"state": "open"})
        return True

    def action_done(self):
        for rec in self:
            if rec.distance_total == 0:
                raise UserError(_("Cannot set done a map sheet which distance equal with zero."))

        self.write({"state": "done"})
        for map_sheet in self:
            map_sheet.log_fuel_ids.write({"state": "done"})
        return True


class FleetRouteLog(models.Model):
    _name = "fleet.route.log"
    _description = "Route Log"
    _order = "date_begin"

    @api.model
    def _get_default_date_begin(self):
        date_begin = None
        context = self.env.context
        if "date" in context:
            date_begin = fields.Datetime.from_string(context["date"])
            date_end = date_begin
            if context and "route_log_ids" in context:
                route_log_ids = context["route_log_ids"]
                for route_log in route_log_ids:
                    if route_log[0] == 4:
                        route_log_obj = self.browse(route_log[1])
                        date_end = route_log_obj.date_end
                    elif route_log[0] == 0 or route_log[0] == 1:
                        values = route_log[2]
                        if values and "date_end" in values:
                            date_end = fields.Datetime.from_string(values["date_end"])
                    if date_end > date_begin:
                        date_begin = date_end
        return date_begin

    # """
    # @api.model
    # def _get_default_vehicle_id(self):
    #     context =  self.env.context or {}
    #     res = context['vehicle_id'] if context and 'vehicle_id' in context else None
    #     return  res
    # """

    name = fields.Char(compute="_compute_route_name", string="Name", store=False)
    scope_id = fields.Many2one("fleet.scope", string="Scope", states={"done": [("readonly", True)]})
    date_begin = fields.Datetime(
        string="Date Begin", states={"done": [("readonly", True)]}, default=_get_default_date_begin
    )
    date_end = fields.Datetime(
        string="Date End", states={"done": [("readonly", True)]}, default=_get_default_date_begin
    )
    week_day = fields.Integer(compute="_compute_week_day", string="Name", store=False)
    route_id = fields.Many2one("fleet.route", string="Route", states={"done": [("readonly", True)]})
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        states={"done": [("readonly", True)]},
    )  # default=_get_default_vehicle_id )
    map_sheet_id = fields.Many2one(
        "fleet.map.sheet",
        string="Map Sheet",
        domain="['&',('vehicle_id','=',vehicle_id),('date_start','<=',date_begin),('date_end','>=',date_end)]",
    )
    distance = fields.Float(string="Distance", states={"done": [("readonly", True)]})
    full = fields.Boolean()
    dist_c1 = fields.Float(string="Dist C1", states={"done": [("readonly", True)]})
    dist_c2 = fields.Float(string="Dist C2", states={"done": [("readonly", True)]})
    dist_c3 = fields.Float(string="Dist C3", states={"done": [("readonly", True)]})
    dist_echiv = fields.Float(string="Equivalence Distance", compute="_compute_dist_echiv", store=True)
    norm_cons = fields.Float(
        compute="_compute_dist_echiv",
        string="Normal Consumption",
        store=True,
        help="The Normal Consumption",
        states={"done": [("readonly", True)]},
    )
    state = fields.Selection(
        [("draft", "Draft"), ("done", "Done")],
        string="Status",
        default="draft",
        help="When the Route Log is created the status is set to 'Draft'.\n\
                                      When the Route Log is closed, the status is set to 'Done'.",
    )

    @api.depends("dist_c1", "dist_c2", "dist_c3")
    def _compute_dist_echiv(self):
        # daca modifc consumul la la o masina nu trebuie sa modific toate foile din urma, 'vehicle_id.avg_cons')
        for item in self:
            item.dist_echiv = item.dist_c1 + 1.1 * item.dist_c2 + 1.4 * item.dist_c3
            if item.vehicle_id:
                item.norm_cons = item.distance * item.vehicle_id.avg_cons / 100

    @api.depends("route_id.name")
    def _compute_route_name(self):
        for item in self:
            if item.route_id:
                item.name = item.route_id.name
            else:
                item.name = "Noname"

    @api.depends("date_begin")
    def _compute_week_day(self):
        for item in self:
            date_int = fields.Datetime.from_string(item.date_begin)
            item.week_day = date_int.strftime("%w")

    @api.constrains("date_begin", "date_end")
    def _check_dates(self):
        for item in self:
            if item.date_begin > item.date_end:
                raise ValidationError(_("Route end-date must be greater then route begin-date"))

    #     """
    #     def _check_dates(self, cr, uid, ids, context=None):
    #         if context == None:
    #             context = {}
    #         route_log = self.browse(cr, uid, ids[0], context=context)
    #         start = route_log.date_begin or False
    #         end = route_log.date_end or False
    #         if start and end :
    #             if start > end:
    #                 return False
    # ##            else:
    # ##                res = self.search(cr, uid, [('vehicle_id','=',route_log.vehicle_id.id),('date_begin')])
    # ##    start < date_begin < end or date_begin < start < date_end
    #         return True
    #
    #     _constraints = [
    #         (_check_dates, 'Error ! Route end-date must be greater then route start-begin', ['date_begin','date_end'])
    #     ]
    #     """

    @api.onchange("route_id", "date_begin")
    def on_change_route(self):

        domain = []
        if self.map_sheet_id:
            prev_route_log = None
            for route_log in self.map_sheet_id.route_log_ids:
                if route_log.date_end <= self.date_begin:
                    prev_route_log = route_log
            if prev_route_log:
                domain = domain.append(("from_loc_id", "=", prev_route_log.route_id.to_loc_id.id))

        if self.route_id and self.date_begin:
            date_int = fields.Datetime.from_string(self.date_begin)
            week_day = int(date_int.strftime("%w"))
            date_end = date_int  # datetime.strptime(date_begin,tools.DEFAULT_SERVER_DATETIME_FORMAT)
            date_end = date_end + timedelta(
                hours=int(math.floor(self.route_id.duration)), minutes=int((self.route_id.duration % 1) * 60)
            )
            date_end = fields.Datetime.to_string(date_end)
            self.distance = self.route_id.distance
            self.dist_c1 = self.route_id.dist_c1
            self.dist_c2 = self.route_id.dist_c2
            self.dist_c3 = self.route_id.dist_c3
            self.date_end = date_end
            self.week_day = week_day

    # def unlink(self):
    #     """ Allows to delete route log in draft states """
    #     for rec in self:
    #         if rec.state not in ["draft", False]:
    #             raise UserError(_("Cannot delete a route log which is in state '%s'.") % (rec.state,))
    #     return super(FleetRouteLog, self).unlink()
