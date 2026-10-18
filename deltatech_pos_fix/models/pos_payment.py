from odoo import models


class PosPayment(models.Model):
    _inherit = "pos.payment"

    def _get_receivable_lines_for_invoice_reconciliation(self, receivable_account):
        # Restul în numerar este lipit de plata în numerar în aceeași notă (_create_payment_moves),
        # deci semnul notei este dat de plată. Restul negativ ar selecta și debitul notei, care,
        # când contul de creanțe POS este același cu al clientului (4111), se stinge cu creditul
        # notei în locul facturii.
        merged_change = self.filtered(
            lambda p: p.is_change and (p.account_move_id.pos_payment_ids - p).filtered(lambda o: not o.is_change)
        )
        return super(PosPayment, self - merged_change)._get_receivable_lines_for_invoice_reconciliation(
            receivable_account
        )
