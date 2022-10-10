# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, models


class ServiceEquipment(models.Model):
    _inherit = "service.equipment"

    def get_context_default(self):
        context = {
            "default_equipment_id": self.id,
            "default_partner_id": self.partner_id.id,
            "default_contact_id": self.contact_id.id,
        }
        return context

    def notification_button(self):
        notifications = self.env["service.notification"].search([("equipment_id", "in", self.ids)])
        context = self.get_context_default()
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
        context = self.get_context_default()
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
