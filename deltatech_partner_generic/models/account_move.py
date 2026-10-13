# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models
from odoo.exceptions import UserError

CUSTOMER_INVOICE_TYPES = ("out_invoice", "out_refund")


class AccountMove(models.Model):
    _inherit = "account.move"

    def _generic_partner_invoices(self):
        """Customer invoices addressed to the generic partner of their own company.

        The generic partner stands for anonymous customers: a real invoice must
        name a real customer, otherwise the document is unusable both for the
        customer and for the e-invoicing flows. Both the invoicing and the
        delivery address are checked.

        Returns a ``{move: field_name}`` mapping of the offending moves.
        """
        result = {}
        for move in self:
            if move.move_type not in CUSTOMER_INVOICE_TYPES:
                continue
            # sudo: the generic partner may be out of reach for the current user
            generic_partner = move.company_id.sudo().generic_partner_id
            if not generic_partner:
                continue
            for field_name in ("partner_id", "partner_shipping_id"):
                partner = move[field_name]
                if generic_partner in (partner | partner.commercial_partner_id):
                    result[move] = field_name
                    break
        return result

    def _post(self, soft=True):
        blocked = self._generic_partner_invoices()
        if blocked:
            move, field_name = next(iter(blocked.items()))
            label = move._fields[field_name].get_description(self.env)["string"]
            raise UserError(
                self.env._(
                    "%(invoice)s cannot be validated: “%(partner)s” is the generic "
                    "partner, used for anonymous customers, and it is set as %(field)s. Set the "
                    "real customer on the invoice before validating it.",
                    invoice=move.display_name,
                    partner=move[field_name].sudo().display_name,
                    field=label,
                )
            )
        return super()._post(soft=soft)
