# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models


class Partner(models.Model):
    _inherit = "res.partner"

    def _get_partner_party_identification_vals_list(self, partner):
        res = super()._get_partner_party_identification_vals_list(partner)
        res += [
            {
                "id_attrs": {"schemeID": "0088"},
                "id": partner.gln,
            }
        ]
        return res
