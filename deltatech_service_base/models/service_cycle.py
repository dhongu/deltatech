# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details

from datetime import timedelta

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ServiceCycle(models.Model):
    _name = "service.cycle"
    _description = "Cycle"

    name = fields.Char(string="Cycle", translate=True)
    value = fields.Integer(string="Value")
    unit = fields.Selection(
        [("day", "Day"), ("week", "Week"), ("month", "Month"), ("year", "Year")],
        string="Unit Of Measure",
        help="Unit of Measure for Cycle.",
    )

    @api.model
    def get_cycle(self):
        self.ensure_one()
        if self.unit == "day":
            return timedelta(days=self.value)
        if self.unit == "week":
            return timedelta(weeks=self.value)
        if self.unit == "month":
            return relativedelta(months=+self.value)  # monthdelta(self.value)
        if self.unit == "year":
            return relativedelta(years=+self.value)
