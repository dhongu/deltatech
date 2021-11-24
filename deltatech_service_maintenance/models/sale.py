# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    notification_id = fields.Many2one("service.notification", string="Notification", readonly=True)

    @api.model
    @api.returns("self", lambda value: value.id)
    def create(self, vals):
        notification_id = self.env.context.get("notification_id", False)
        if notification_id:
            vals["notification_id"] = notification_id

        order = super(SaleOrder, self).create(vals)
        notification_id = self.env.context.get("notification_id", False)
        if notification_id:
            notification = self.env["service.notification"].browse(notification_id)
            notification.write({"sale_order_id": order.id})
        return order

    def new_notification(self):
        self.ensure_one()
        context = {
            "default_category": "sale",
            "default_partner_id": self.partner_id.id,
            "default_address_id": self.partner_shipping_id.id,
        }

        if self.order_line:

            context["default_item_ids"] = []

            for item in self.order_line:
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
