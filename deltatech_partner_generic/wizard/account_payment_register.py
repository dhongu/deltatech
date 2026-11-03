# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    def _get_batch_available_journals(self, batch_result):
        journals = super()._get_batch_available_journals(batch_result)
        generic_partner = batch_result["lines"].company_id.generic_partner_id
        if generic_partner and batch_result["payment_values"]["partner_id"] in generic_partner.ids:
            journals = journals.filtered(lambda journal: not journal.restriction and journal.type in ("bank", "cash"))
        return journals

    @api.depends("available_journal_ids")
    def _compute_journal_id(self):
        res = super()._compute_journal_id()
        for wizard in self:
            # the journal of the invoice preferred payment method skips the domain
            allowed = wizard.available_journal_ids._origin
            if wizard.journal_id.restriction and wizard.journal_id._origin not in allowed:
                wizard.journal_id = allowed[:1]
        return res
