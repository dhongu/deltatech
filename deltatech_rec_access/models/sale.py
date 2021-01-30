# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import _, api, models
from odoo.exceptions import UserError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def action_button_confirm(self):
        group_ext_id = "deltatech_rec_access.group_sale_order_no_confirm"
        res = self.env["res.users"].has_group(group_ext_id)
        if res:
            raise UserError(_("You can not have authorization to confirm sale order."))
        return super(SaleOrder, self).action_button_confirm()
