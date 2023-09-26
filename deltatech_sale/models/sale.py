# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, api, models
from odoo.exceptions import UserError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    @api.onchange("product_id")
    def _onchange_product_id_warning(self):
        if not self.order_id.partner_id:
            raise UserError(_("Before choosing a product,\n select a customer in the sales form."))

        result = super()._onchange_product_id_warning()

        return result
