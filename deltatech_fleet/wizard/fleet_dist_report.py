# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class FleetDistanceReport(models.Model):
    _name = "fleet.distance.report"
    _description = "FleetDistanceReport"

    date_from = fields.Date("Start Date", required=True, default=fields.Date.today)
    date_to = fields.Date("End Date", required=True, default=fields.Date.today)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)

    @api.model
    def default_get(self, fields_list):
        res = super(FleetDistanceReport, self).default_get(fields_list)

        today = fields.Date.context_today(self)
        today = fields.Date.from_string(today)

        from_date = today + relativedelta(day=1, months=0)
        to_date = today + relativedelta(day=1, months=1, days=-1)

        res["date_from"] = fields.Date.to_string(from_date)
        res["date_to"] = fields.Date.to_string(to_date)

        return res

    def do_compute(self):
        domain = [
            ("date_start", ">=", self.date_from),
            ("date_start", "<=", self.date_to),
            ("company_id", "=", self.company_id.id),
        ]
        costs = self.env["fleet.vehicle.cost.report"].read_group(
            domain=domain, fields=["company_id", "vehicle_id", "cost"], groupby=["company_id", "vehicle_id"], lazy=False
        )
        lines = []
        for line in costs:
            distance = self.get_distance(line["vehicle_id"][0])
            price = 0
            if distance:
                price = line["cost"] / distance
            lines += [
                {
                    "report_id": self.id,
                    "company_id": self.company_id.id,
                    "vehicle_id": line["vehicle_id"][0],
                    "cost": line["cost"],
                    "distance": distance,
                    "price": price,
                }
            ]

        self.env["fleet.distance.report.line"].create(lines)

    def get_distance(self, vehicle_id):
        distance = 0
        date_start = self.date_from + relativedelta(hour=0, minute=0)
        date_end = self.date_to + relativedelta(hour=23, minute=59)
        domain = [("vehicle_id", "=", vehicle_id), ("date", "<", date_start)]
        odometer_start = self.env["fleet.vehicle.odometer"].search(domain, order="date desc", limit=1)
        if not odometer_start:
            domain = [("vehicle_id", "=", vehicle_id), ("date", "<", date_end)]
            odometer_start = self.env["fleet.vehicle.odometer"].search(domain, order="date", limit=1)

        domain = [("vehicle_id", "=", vehicle_id), ("date", ">=", date_end)]
        odometer_end = self.env["fleet.vehicle.odometer"].search(domain, order="date", limit=1)

        if not odometer_end:
            domain = [("vehicle_id", "=", vehicle_id), ("date", ">", date_start)]
            odometer_end = self.env["fleet.vehicle.odometer"].search(domain, order="date desc", limit=1)

        if odometer_start and odometer_end:
            distance = odometer_end.value - odometer_start.value

        return distance

    def button_show_report(self):
        self.do_compute()
        action = self.env["ir.actions.actions"]._for_xml_id("deltatech_fleet.action_fleet_distance_report_line")
        action["domain"] = [("report_id", "=", self.id)]
        return action


class FleetDistanceReportLine(models.Model):
    _name = "fleet.distance.report.line"
    _description = "FleetDistanceReportLine"

    report_id = fields.Many2one("fleet.distance.report")
    company_id = fields.Many2one("res.company", "Company", readonly=True)
    vehicle_id = fields.Many2one("fleet.vehicle", "Vehicle", readonly=True)
    cost = fields.Float("Cost", readonly=True)
    distance = fields.Float("Distance", readonly=True)
    price = fields.Float("Price", readonly=True, group_operator="avg")
