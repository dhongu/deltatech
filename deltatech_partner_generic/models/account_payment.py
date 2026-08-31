# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.depends("payment_type", "partner_id", "company_id.generic_partner_id")
    def _compute_available_journal_ids(self):
        super()._compute_available_journal_ids()
        for payment in self:
            generic_partner = payment.company_id.generic_partner_id
            if generic_partner and payment.partner_id == generic_partner:
                payment.available_journal_ids = payment.available_journal_ids.filtered(
                    lambda journal: not journal.restriction and journal.type in ("bank", "cash")
                )
