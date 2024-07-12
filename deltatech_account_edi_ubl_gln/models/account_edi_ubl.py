# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class AccountEdiXmlUBL20(models.AbstractModel):
    _inherit = "account.edi.xml.ubl_20"

    def _get_partner_party_identification_vals_list(self, partner):
        res = super()._get_partner_party_identification_vals_list(partner)
        if partner.gln:
            res += [{"id_attrs": {"schemeID": "0088"}, "id": partner.gln}]
        return res
