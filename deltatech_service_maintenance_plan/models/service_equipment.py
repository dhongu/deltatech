# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class ServiceEquipment(models.Model):
    _inherit = "service.equipment"

    plan_ids = fields.One2many("service.plan", "equipment_id", string="Plans")

    # cand a fost facuta ultima revizie ? si trebuie putin modificata
    last_call_done = fields.Date(string="Last call done", compute="_compute_last_call_done")

    def _compute_last_call_done(self):

        plans = self.env["service.plan"].search([("equipment_id", "=", self.id), ("state", "=", "active")])
        if plans:
            calls = self.env["service.plan.call"].search(
                [("plan_id", "in", plans.ids), ("state", "=", "completion")], order="completion_date DESC", limit=1
            )
            if calls:
                self.last_call_done = calls.completion_date
