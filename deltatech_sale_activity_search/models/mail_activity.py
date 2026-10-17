from odoo import api, models


class MailActivity(models.Model):
    _inherit = "mail.activity"

    def _get_sale_orders(self):
        order_ids = {activity.res_id for activity in self if activity.res_model == "sale.order" and activity.res_id}
        return self.env["sale.order"].browse(order_ids).exists()

    @api.model_create_multi
    def create(self, vals_list):
        activities = super().create(vals_list)
        activities._get_sale_orders().set_active_activity_types()
        return activities

    def write(self, vals):
        orders = self._get_sale_orders()
        res = super().write(vals)
        orders |= self._get_sale_orders()
        orders.invalidate_recordset(["activity_ids"])
        orders.set_active_activity_types()
        return res

    def unlink(self):
        orders = self._get_sale_orders()
        res = super().unlink()
        orders.set_active_activity_types()
        return res
