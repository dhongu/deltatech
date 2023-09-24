# ©  2015-2022 Deltatech
# See README.rst file on addons root folder for license details


from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class ServiceDateRange(models.Model):
    _name = "service.date.range"
    _description = "Date Range"

    name = fields.Char(string="Data Range")
    date_start = fields.Date(string="Start date", required=True)
    date_end = fields.Date(string="End date", required=True)
    active = fields.Boolean(
        help="The active field allows you to hide the date range without " "removing it.",
        default=True,
    )

    _sql_constraints = [
        (
            "date_range_uniq",
            "unique (name, active)",
            "A date range must be unique!",
        )
    ]

    @api.model
    def generate_date_range(self):
        date_start = fields.Date.today().replace(month=1, day=1)
        for _i in range(12):
            date_end = date_start + relativedelta(months=1, days=-1)
            name = date_start.strftime("%Y/%m")
            if not self.search([("name", "=", name)]):
                self.create(
                    {
                        "name": name,
                        "date_start": date_start,
                        "date_end": date_end,
                    }
                )
            date_start = date_start + relativedelta(months=1)
