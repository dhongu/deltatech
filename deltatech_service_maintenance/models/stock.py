# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = "stock.picking"

    notification_id = fields.Many2one("service.notification", string="Notification", readonly=True)
    service_order_id = fields.Many2one("service.order", string="Service Order", readonly=True)
    warranty_id = fields.Many2one("service.warranty", string="Warranty", readonly=True, copy=False)

    @api.model
    @api.returns("self", lambda value: value.id)
    def create(self, vals):
        res = super().create(vals)
        if res:
            notification_id = self.env.context.get("notification_id", False)
            warranty_id = self.env.context.get("warranty_id", False)

            if notification_id:
                res.notification_id = notification_id
                notification = self.env["service.notification"].browse(notification_id)
                notification.write({"piking_id": res.id})

            if warranty_id:
                res.warranty_id = warranty_id
                warranty = self.env["service.warranty"].browse(warranty_id)
                warranty.write({"picking_id": res.id})
        return res

    def new_notification(self):
        self.ensure_one()
        context = {"default_partner_id": self.partner_id.id}

        if self.move_lines:
            context["default_item_ids"] = []

            for item in self.move_lines:
                value = {}
                value["product_id"] = item.product_id.id
                value["quantity"] = item.product_uom_qty
                context["default_item_ids"] += [(0, 0, value)]

        context["sale_order_id"] = self.id
        return {
            "name": _("Notification"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "service.notification",
            "view_id": False,
            "views": [[False, "form"]],
            "context": context,
            "type": "ir.actions.act_window",
        }


class StockLot(models.Model):
    _inherit = "stock.production.lot"

    def action_lot_open_warranty(self):
        self.ensure_one()
        equipments = self.env["service.equipment"].search([("serial_id", "=", self.id)])
        if equipments:
            warranties = self.env["service.warranty"].search([("equipment_id", "in", equipments.ids)])
            if warranties:
                action = {
                    "res_model": "service.warranty",
                    "type": "ir.actions.act_window",
                    "name": _("Warranties for serial %s", self.name),
                    "domain": [("id", "in", warranties.ids)],
                    "view_mode": "tree,form",
                }
                return action
        raise UserError(_("No warranties for this serial!"))
