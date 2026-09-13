# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class AccountEdiCommon(models.AbstractModel):
    _inherit = "account.edi.common"

    def _get_uom_unece_code(self, uom):
        """Prefer the code configured on the unit over the built-in mapping.

        This module exists because `account_edi_ubl_cii` does NOT go through
        `uom.uom._get_unece_code()`. It keeps a second copy of the same logic on
        this abstract model, reading the core dictionary directly
        (`account_edi_ubl_cii/models/account_edi_common.py`). Without the
        override below, a code set on the unit would apply to eTransport and be
        ignored on invoices — silently, since both paths still produce a
        schema-valid document.

        The dependency lives in its own auto-installing bridge so that
        `deltatech_uom_unece` stays usable on databases that send no UBL or CII
        invoice at all.
        """
        return uom.unece_code_id.code or super()._get_uom_unece_code(uom)
