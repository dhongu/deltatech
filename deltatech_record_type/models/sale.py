from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    so_type = fields.Many2one("record.type", string="Order Type", tracking=True)

    def action_confirm(self):
        for order in self:
            if not self.env.user.has_group("deltatech_record_type.group_confirm_order_without_record_type"):
                if not order.so_type:
                    raise exceptions.UserError(
                        _("You do not have the rights to confirm an order without specifying an Order Type.")
                    )
        return super().action_confirm()

    @api.onchange("so_type")
    def _onchange_so_type(self):
        for default_value in self.so_type.default_values_ids:
            self[default_value.field_name] = safe_eval(default_value.field_value)
