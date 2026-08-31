from odoo import models
from odoo.exceptions import UserError

CUSTOMER_INVOICE_TYPES = ("out_invoice", "out_refund")


class AccountMove(models.Model):
    _inherit = "account.move"

    def _generic_partner_invoices(self):
        """Customer invoices issued to the generic partner of their own company.

        The generic partner stands for anonymous customers: a real invoice must
        name a real customer, otherwise the document is unusable both for the
        customer and for the e-invoicing flows.
        """
        moves = self.browse()
        for move in self:
            if move.move_type not in CUSTOMER_INVOICE_TYPES:
                continue
            # sudo: the generic partner may be out of reach for the current user
            generic_partner = move.company_id.sudo().generic_partner_id
            if not generic_partner:
                continue
            partners = move.partner_id | move.partner_id.commercial_partner_id
            if generic_partner in partners:
                moves |= move
        return moves

    def _post(self, soft=True):
        blocked = self._generic_partner_invoices()
        if blocked:
            move = blocked[0]
            raise UserError(
                self.env._(
                    "The invoice %(invoice)s cannot be validated: “%(partner)s” is the generic "
                    "partner, used for anonymous customers. Set the real customer on the invoice "
                    "before validating it.",
                    invoice=move.display_name,
                    partner=move.partner_id.sudo().display_name,
                )
            )
        return super()._post(soft=soft)
