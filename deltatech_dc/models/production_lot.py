# ©  2008-2022 Deltatech
# See README.rst file on addons root folder for license details

import datetime

from odoo import api, fields, models


class StockProductionLot(models.Model):
    _inherit = "stock.lot"

    production_date = fields.Datetime()

    def _get_dates(self, product_id=None):
        """Returns dates based on number of days configured in current lot's product."""
        mapped_fields = {
            "expiration_date": "expiration_time",
            "use_date": "use_time",
            "removal_date": "removal_time",
            "alert_date": "alert_time",
        }
        res = dict.fromkeys(mapped_fields, False)
        product = self.env["product.product"].browse(product_id) or self.product_id

        production_date = self.production_date or datetime.datetime.now()
        if product:
            for field in mapped_fields:
                duration = getattr(product, mapped_fields[field])
                if duration:
                    date = production_date + datetime.timedelta(days=duration)
                    res[field] = fields.Datetime.to_string(date)
        return res

    @api.onchange("production_date")
    def onchange_production_date(self):
        if not self.production_date:
            self.production_date = self.create_date
