# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class Website(models.Model):
    _inherit = "website"

    def _prepare_sale_order_values(self, partner, pricelist):
        values = super(Website, self)._prepare_sale_order_values(partner, pricelist)
        web_user_id = self.env.context.get("uid", False)
        web_user = self.env["res.users"].sudo().search([("id", "=", web_user_id)])
        if web_user and web_user.delivery_address_id:
            values["partner_shipping_id"] = web_user.delivery_address_id.id
        return values
