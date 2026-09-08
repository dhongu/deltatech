# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class Website(models.Model):
    _inherit = "website"

    def _prepare_sale_order_values(self, partner_sudo):
        values = super()._prepare_sale_order_values(partner_sudo)
        web_user_id = self.env.context.get("uid") or self.env.uid
        web_user = self.env["res.users"].sudo().browse(web_user_id).exists()
        if web_user and web_user.delivery_address_id:
            values["partner_shipping_id"] = web_user.delivery_address_id.id
        return values
