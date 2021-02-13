# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, fields, models


class ServiceEquipment(models.Model):
    _inherit = "service.equipment"

    plan_ids = fields.One2many("service.plan", "equipment_id", string="Plans")

    # canda a fost facuta ultima revizie ? si trebuie putin modificata
    last_call_done = fields.Date(string="Last call done", compute="_compute_last_call_done")

    def _compute_last_call_done(self):

        plans = self.env["service.plan"].search([("equipment_id", "=", self.id), ("state", "=", "active")])
        if plans:
            calls = self.env["service.plan.call"].search(
                [("plan_id", "in", plans.ids), ("state", "=", "completion")], order="completion_date DESC", limit=1
            )
            if calls:
                self.last_call_done = calls.completion_date

    def notification_button(self):
        notifications = self.env["service.notification"].search([("equipment_id", "in", self.ids)])
        context = {
            "default_equipment_id": self.id,
            "default_partner_id": self.partner_id.id,
            "default_agreement_id": self.agreement_id.id,
            "default_address_id": self.address_id.id,
            "default_contact_id": self.contact_id.id,
        }
        return {
            "domain": "[('id','in', [" + ",".join(map(str, notifications.ids)) + "])]",
            "name": _("Notifications"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "service.notification",
            "view_id": False,
            "context": context,
            "type": "ir.actions.act_window",
        }

    def order_button(self):
        orders = self.env["service.order"].search([("equipment_id", "in", self.ids)])
        context = {
            "default_equipment_id": self.id,
            "default_partner_id": self.partner_id.id,
            "default_agreement_id": self.agreement_id.id,
            "default_address_id": self.address_id.id,
            "default_contact_id": self.contact_id.id,
        }
        return {
            "domain": "[('id','in', [" + ",".join(map(str, orders.ids)) + "])]",
            "name": _("Orders"),
            "view_type": "form",
            "view_mode": "tree,form",
            "res_model": "service.order",
            "view_id": False,
            "context": context,
            "type": "ir.actions.act_window",
        }
