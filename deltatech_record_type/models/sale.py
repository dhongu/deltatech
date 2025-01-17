from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval


class SaleOrder(models.Model):
    _inherit = "sale.order"

    so_type = fields.Many2one("record.type", string="Order Type", tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not self.env.user.has_group("deltatech_record_type.group_create_order_without_record_type"):
                if not vals.get("so_type"):
                    raise exceptions.UserError(
                        _("You do not have the rights to create an order without specifying an Order Type.")
                    )
        return super().create(vals_list)

    def write(self, vals):
        for order in self:
            if not self.env.user.has_group("deltatech_record_type.group_create_order_without_record_type"):
                if "so_type" not in vals and not order.so_type:
                    raise exceptions.UserError(_("You do not have the rights to remove the Order Type from an order."))
        return super().write(vals)

    @api.onchange("so_type")
    def _onchange_so_type(self):
        for default_value in self.so_type.default_values_ids:
            self[default_value.field_name] = safe_eval(default_value.field_value)
