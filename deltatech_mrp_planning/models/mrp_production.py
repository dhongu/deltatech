# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from datetime import timedelta

from odoo import api, fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    date_planned_start_wo = fields.Datetime(string="Planned Start Date", index=True)
    date_planned_finished_wo = fields.Datetime(string="Planned Finished date", index=True)

    @api.multi
    def button_plan(self):
        res = super(MrpProduction, self).button_plan()

        # todo: de facut planificarea inapoi!
        for production in self:
            planned_date = production.date_planned_start  # la data asta trebuie sa inceapa
            production_values = {"date_planned_start_wo": False, "date_planned_finished_wo": False}
            values = {}
            workorders = production.workorder_ids  # .sorted(key=id, reverse=True)

            for workorder in workorders:

                date_start = planned_date
                date_end = date_start + timedelta(minutes=workorder.duration_expected)
                workcenter = workorder.workcenter_id

                date_start = workcenter.resource_calendar_id.plan_hours(
                    0, date_start, compute_leaves=True, resource=workcenter.resource_id
                )
                date_end = workcenter.resource_calendar_id.plan_hours(
                    workorder.duration_expected / 60.0, date_start, compute_leaves=True, resource=workcenter.resource_id
                )

                if not production_values["date_planned_start_wo"]:
                    production_values["date_planned_start_wo"] = date_start
                planned_date = date_end
                values["date_planned_start"] = date_start
                values["date_planned_finished"] = date_end
                workorder.write(values)
            production_values["date_planned_finished_wo"] = planned_date
            production.write(production_values)
        return res

    @api.multi
    def button_unplan(self):

        for production in self:
            production.workorder_ids.write({"date_planned_start": False, "date_planned_finished": False})
        self.write({"date_planned_start_wo": False, "date_planned_finished_wo": False})
