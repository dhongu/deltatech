# ©  2015-2020 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.multi
    def post(self):
        """ Mostenire functie post pentru selectarea seriei.
        seria standard ar trebui dezactivata
        """

        for rec in self:
            if rec.partner_type == "customer":
                if not rec.name and rec.payment_type != "transfer":
                    if rec.journal_id:
                        rec.sudo().journal_id.sequence_id.number_next = (
                            rec.journal_id.sequence_id.number_next - 1
                        )  # conflicts with account.move sequence
                        rec.name = rec.journal_id.sequence_id.next_by_id()
                        pass
        return super(AccountPayment, self).post()
