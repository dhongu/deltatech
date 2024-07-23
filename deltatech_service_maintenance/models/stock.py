# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    notification_id = fields.Many2one("service.notification", string="Notification", readonly=True)
    service_order_id = fields.Many2one("service.order", string="Service Order", readonly=True)

    @api.model_create_multi
    @api.returns("self", lambda value: value.id)
    def create(self, vals_list):
        notification_id = self.env.context.get("notification_id", False)
        for vals in vals_list:
            if notification_id:
                vals["notification_id"] = notification_id
        picking = super().create(vals_list)

        if notification_id and picking:
            notification = self.env["service.notification"].browse(notification_id)
            notification.write({"piking_id": picking[0].id})
        return picking

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
