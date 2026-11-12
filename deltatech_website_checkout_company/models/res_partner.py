# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import re

from stdnum.util import get_cc_module

from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def _tb_clean_company_vat(self, vat):
        """The VAT number as typed on the website, without spaces and dots, upper case
        (e.g. "ro 123.456" -> "RO123456")."""
        return re.sub(r"[\s.\-]", "", vat or "").upper()

    @api.model
    def _tb_is_valid_company_vat(self, vat):
        """Whether a Romanian company identifier (CUI, with or without the RO prefix) is valid."""
        vat = self._tb_clean_company_vat(vat)
        if not vat:
            return False
        return get_cc_module("ro", "vat").is_valid(vat)

    @api.model
    def _tb_find_company_by_vat(self, vat, company=None):
        """The company partner already recorded with this VAT number, with or without the RO
        prefix; empty when none. The partners of another company are left out."""
        vat = self._tb_clean_company_vat(vat)
        digits = vat.removeprefix("RO")
        if not digits:
            return self.browse()
        domain = [
            ("vat", "in", [digits, f"RO{digits}"]),
            ("is_company", "=", True),
            ("parent_id", "=", False),
        ]
        if company:
            domain.append(("company_id", "in", [False, company.id]))
        return self.sudo().search(domain, order="id", limit=1)
