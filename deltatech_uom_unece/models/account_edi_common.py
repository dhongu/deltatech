# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class AccountEdiCommon(models.AbstractModel):
    _inherit = "account.edi.common"

    def _get_uom_unece_code(self, uom):
        """Prefer the code configured on the unit over the built-in mapping.

        This override is needed because `account_edi_ubl_cii` does NOT go
        through `uom.uom._get_unece_code()`. It keeps a second copy of the same
        logic on this abstract model, reading the core dictionary directly
        (`account_edi_ubl_cii/models/account_edi_common.py`). Overriding only the
        method on `uom.uom` would apply the configured code to eTransport and
        ignore it on invoices — silently, since both paths still produce a
        schema-valid document.
        """
        return uom.unece_code_id.code or super()._get_uom_unece_code(uom)
