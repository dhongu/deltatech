from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    active_activity_types = fields.Char(string="Active Activity Types", readonly=1)

    def set_active_activity_types(self):
        for order in self:
            activity_types = order.activity_ids.mapped("activity_type_id.name")
            order.active_activity_types = ", ".join(activity_types)
