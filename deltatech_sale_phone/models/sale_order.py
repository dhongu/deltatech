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
            order.partner_phone = order.partner_id.phone or False
