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

        warranty_id = self.env.context.get("warranty_id", False)
        if warranty_id:
            picking.warranty_id = warranty_id
            warranty = self.env["service.warranty"].browse(warranty_id)
            warranty.write({"picking_id": picking.id})
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

    def button_validate(self):
        """
        Write the actual values in warranty
        """
        res = super().button_validate()
        for picking in self:
            if picking.warranty_id:
                for move in picking.move_ids:
                    value = 0.0
                    for layer in move.stock_valuation_layer_ids:
                        value = +layer.value
                    line = picking.warranty_id.item_ids.filtered(
                        lambda p, product_id=move.product_id: p.product_id == product_id
                    )
                    if not line or len(line) > 1:
                        raise UserError(_("No lines or multiple lines in linked warranty found"))
                    else:
                        line.write({"price_unit": value / line.quantity if line.quantity else 0.0})
        return res


class StockLot(models.Model):
    _inherit = "stock.lot"

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
                    "view_mode": "list,form",
                }
                return action
        raise UserError(_("No warranties for this serial!"))
