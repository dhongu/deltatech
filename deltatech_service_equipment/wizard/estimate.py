# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


import threading

from odoo import _, api, fields, models


class ServiceMeterReadingEstimate(models.TransientModel):
    _name = "service.meter.reading.estimate"
    _description = "Meter Reading Estimate"

    period_id = fields.Many2one(
        "account.period",
        string="Period",
        domain=[("state", "!=", "done")],
        required=True,
    )

    meter_ids = fields.Many2many("service.meter", "service_meter_estimate", "estimate_id", "meter_id", string="Meters")

    @api.model
    def default_get(self, fields_list):
        defaults = super(ServiceMeterReadingEstimate, self).default_get(fields_list)

        active_ids = self.env.context.get("active_ids", False)

        if active_ids:
            domain = [("id", "in", active_ids)]
        else:
            domain = []
        res = self.env["service.meter"].search(domain)
        defaults["meter_ids"] = [(6, 0, [rec.id for rec in res])]
        return defaults

    def do_estimation(self):
        threaded_estimation = threading.Thread(target=self._background_estimation)
        threaded_estimation.start()
        return {"type": "ir.actions.act_window_close"}

    def _background_estimation(self):
        with api.Environment.manage():
            new_cr = self.pool.cursor()
            self = self.with_env(self.env(cr=new_cr))
            self._calc_estimation(new_cr)
            new_cr.commit()
            new_cr.close()

        return {}

    def _calc_estimation(self):

        domain_date = [("date", ">=", self.period_id.date_start), ("date", "<=", self.period_id.date_end)]
        for meter in self.meter_ids:
            domain = domain_date + [("meter_id", "=", meter.id)]
            reading = self.env["service.meter.reading"].search(domain, limit=1)
            if not reading:
                self.env["service.meter.reading"].create(
                    {
                        "meter_id": meter.id,
                        "equipment_id": meter.equipment_id.id,
                        "date": self.period_id.date_end,
                        "counter_value": meter.get_forcast(self.period_id.date_end),
                        "estimated": True,
                    }
                )

        message = _("Estimation executed in background was terminated")
        self.env.user.post_notification(title=_("Estimation"), message=message)
