# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends("partner_id", "company_id")
    def _compute_preferred_payment_method_line_id(self):
        res = super()._compute_preferred_payment_method_line_id()
        # the default is stored on the commercial partner, a contact does not inherit it
        for move in self.filtered(lambda m: not m.preferred_payment_method_line_id and m.partner_id):
            partner = move.partner_id.commercial_partner_id.with_company(move.company_id)
            if move.is_sale_document():
                move.preferred_payment_method_line_id = partner.property_inbound_payment_method_line_id
            else:
                move.preferred_payment_method_line_id = partner.property_outbound_payment_method_line_id
        return res
