# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import timedelta

import pytz

from odoo import api
from odoo import models, fields


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    date_planned_start_wo = fields.Datetime(string="Scheduled Start Date", index=True)
    date_planned_finished_wo = fields.Datetime(string="Scheduled Start Date", index=True)

    def button_plan(self):
        res = super(MrpProduction, self).button_plan()
        tz_name = self._context.get('tz') or self.env.user.tz
        # todo: de facut planificarea inapoi!
        for production in self:
            # planned_date = fields.Datetime.from_string(self.date_planned_start)  # la data asta trbuie sa inceapa
            planned_date = self.date_planned_start
            production_values = {'date_planned_start_wo': False,
                                 'date_planned_finished_wo': False}
            values = {}
            workorders = production.workorder_ids  # .sorted(key=id, reverse=True)
            for workorder in workorders:

                date_start = planned_date
                date_end = date_start + timedelta(minutes=workorder.duration_expected)

                if workorder.workcenter_id.resource_id:
                    calendar = workorder.workcenter_id.resource_calendar_id
                    date_start = calendar.plan_hours(hours=workorder.duration_expected / 60, day_dt=date_start)
                    date_end = date_start + timedelta(minutes=workorder.duration_expected)


                if not production_values['date_planned_start_wo']:
                    production_values['date_planned_start_wo'] = date_start
                planned_date = date_end
                values['date_planned_start'] = date_start
                values['date_planned_finished'] = date_end
                workorder.write(values)
            production_values['date_planned_finished_wo'] = planned_date
            production.write(production_values)
        return res

    def button_unplan(self):

        for production in self:
            production.workorder_ids.write({'date_planned_start': False,
                                            'date_planned_finished': False})
        self.write({'date_planned_start_wo': False,
                    'date_planned_finished_wo': False})
