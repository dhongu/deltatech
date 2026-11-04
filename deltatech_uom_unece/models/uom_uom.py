# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class UomUom(models.Model):
    _inherit = "uom.uom"

    unece_code_id = fields.Many2one(
        "uom.unece.code",
        string="UNECE Code",
        help="Code sent in electronic documents (e-invoice, eTransport) for this unit, "
        "picked from the ANAF nomenclature. Takes precedence over the UN/ECE Code field "
        "of Odoo; when empty, that field (and then the code built into Odoo) is used.",
    )

    def _get_unece_code(self):
        """Return the code picked on the unit, falling back to the standard chain.

        Since 20.0 `account_edi_ubl_cii` has its own `unece_code` Char field on the
        unit and every electronic document (UBL, CII, eTransport) reads the code
        through this method; the dictionary in `account` is only the last fallback.
        The module stays an extension over that field, for what it does not cover:

        * the code is picked from the nomenclature ANAF publishes with the SAF-T
          schema (over two thousand Rec 20/21 entries, Romanian names), instead of
          being typed by hand;
        * several units may share a code. The standard field is unique
          (`_unece_code_unique`), so "Box of 13 kg" and "Box of 5 kg" cannot both be
          `XBX` there; here they can.

        An explicit pick wins over the standard field rather than only filling in
        for it, so a wrong standard value can be corrected. Leaving the field empty
        changes nothing, which keeps the module safe to install on a running
        database.

        No `ensure_one()`: core copes with an empty recordset — an invoice line
        without a product reaches this through an empty `uom_id` and gets `C62` —
        and `self.unece_code_id.code` is falsy there, so the fallback still runs.
        """
        return self.unece_code_id.code or super()._get_unece_code()
