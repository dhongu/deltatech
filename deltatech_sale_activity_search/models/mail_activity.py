from odoo import api, models


class MailActivity(models.Model):
    _inherit = "mail.activity"

    @api.model
    def create(self, vals):
        activity = super().create(vals)
        if activity.res_model == "sale.order":
            order = self.env["sale.order"].browse(activity.res_id)
            order.set_active_activity_types()
        return activity

    def write(self, vals):
        res = super().write(vals)
        if self.res_model == "sale.order":
            order = self.env["sale.order"].browse(self.res_id)
            order.set_active_activity_types()
        return res

    def unlink(self):
        orders = self.filtered(lambda a: a.res_model == "sale.order").mapped("res_id")
        res = super().unlink()
        for order_id in orders:
            order = self.env["sale.order"].browse(order_id)
            order.set_active_activity_types()
        return res
