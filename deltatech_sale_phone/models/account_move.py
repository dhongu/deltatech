# ©  2008-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    partner_phone = fields.Char(string="Phone", compute="_compute_phone")

    @api.depends("partner_id")
    def _compute_phone(self):
        for move in self:
            if move.partner_id.phone:
                move.partner_phone = move.partner_id.phone
            elif move.partner_id.mobile:
                move.partner_phone = move.partner_id.mobile
            else:
                move.partner_phone = False
