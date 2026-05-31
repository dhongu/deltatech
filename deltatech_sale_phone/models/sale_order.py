# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_phone = fields.Char(string="Phone", compute="_compute_phone")

    @api.depends("partner_id")
    def _compute_phone(self):
        for order in self:
            if order.partner_id.phone:
                order.partner_phone = order.partner_id.phone
            elif order.partner_id.mobile:
                order.partner_phone = order.partner_id.mobile
            else:
                order.partner_phone = False
