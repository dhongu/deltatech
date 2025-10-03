from odoo import api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    so_type = fields.Many2one("record.type", string="Order Type", tracking=True)
    show_so_type = fields.Boolean(compute="_compute_show_so_type", store=False)

    def action_confirm(self):
        for order in self:
            if hasattr(order, "website_id") and order.website_id:
                continue
            if (
                not self.env.user.has_group("deltatech_record_type.group_confirm_order_without_record_type")
                and order.show_so_type
            ):
                if not order.so_type:
                    raise exceptions.UserError(
                        self.env._("You do not have the rights to confirm an order without specifying an Order Type.")
                    )
        return super().action_confirm()

    @api.onchange("so_type")
    def _onchange_so_type(self):
        for default_value in self.so_type.default_values_ids:
            self[default_value.field_name] = safe_eval(default_value.field_value)

    @api.depends("so_type")  # need a depends or it won't trigger the compute on new
    def _compute_show_so_type(self):
        sale_types = self.env["record.type"].search([("model", "=", "sale.order")])
        for record in self:
            if sale_types:
                record.show_so_type = True
            else:
                record.show_so_type = False


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_procurement_values(self, group_id):
        values = super()._prepare_procurement_values(group_id)
        if not values.get("route_ids") and self.order_id.so_type.route_ids:
            values["route_ids"] = self.order_id.so_type.route_ids
        return values
