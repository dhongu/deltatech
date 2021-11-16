# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class RequiredOrder(models.Model):
    _inherit = "required.order"

    @api.model
    def create(self, vals):
        res = super(RequiredOrder, self).create(vals)
        notification_id = self.env.context.get("notification_id", False)
        if notification_id:
            notification = self.env["service.notification"].browse(notification_id)
            notification.write({"required_order_id": res.id})
        return res
