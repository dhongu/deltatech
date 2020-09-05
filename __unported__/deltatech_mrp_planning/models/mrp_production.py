# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from datetime import timedelta

import pytz

from odoo import api
from odoo import models, fields


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    date_planned_start_wo = fields.Datetime(string="Scheduled Start Date", index=True)
    date_planned_finished_wo = fields.Datetime(string="Scheduled Start Date", index=True)

    @api.multi
    def button_plan(self):
        res = super(MrpProduction, self).button_plan()
        tz_name = self._context.get('tz') or self.env.user.tz
        # todo: de facut planificarea inapoi!
        for production in self:
            planned_date = fields.Datetime.from_string(self.date_planned_start)  # la data asta trbuie sa inceapa
            production_values = {'date_planned_start_wo': False,
                                 'date_planned_finished_wo': False}
            values = {}
            workorders = production.workorder_ids  # .sorted(key=id, reverse=True)
            for workorder in workorders:

                date_start = planned_date
                date_end = date_start + timedelta(minutes=workorder.duration_expected)

                if workorder.workcenter_id.resource_id:
                    calendar = workorder.workcenter_id.calendar_id
                    intervals = calendar.schedule_hours(hours=workorder.duration_expected / 60,
                                                        day_dt=date_start)
                    date_start = intervals and intervals[0][0] or date_start
                    date_end = intervals and intervals[-1][1] or date_end

                    # if tz_name:
                    #    date_start = date_start.astimezone(pytz.UTC)
                    #    date_end = date_end.astimezone(pytz.UTC)

                if not production_values['date_planned_start_wo']:
                    production_values['date_planned_start_wo'] = fields.Datetime.to_string(date_start)
                planned_date = date_end
                values['date_planned_start'] = fields.Datetime.to_string(date_start)
                values['date_planned_finished'] = fields.Datetime.to_string(date_end)
                workorder.write(values)
            production_values['date_planned_finished_wo'] = fields.Datetime.to_string(planned_date)
            production.write(production_values)
        return res

    @api.multi
    def button_unplan(self):

        for production in self:
            production.workorder_ids.write({'date_planned_start': False,
                                            'date_planned_finished': False})
        self.write({'date_planned_start_wo': False,
                    'date_planned_finished_wo': False})
