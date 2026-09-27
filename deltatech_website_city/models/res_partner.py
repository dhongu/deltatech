# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _get_mandatory_address_fields(self, country_sudo, **kwargs):
        # `portal` already swaps the free-text `city` for `city_id` when the city is chosen
        # from the list; the localities come with the state, so the state is required too.
        mandatory_fields = super()._get_mandatory_address_fields(country_sudo, **kwargs)
        if country_sudo._enforce_city_choice() and country_sudo.state_ids:
            mandatory_fields |= {"city_id", "state_id"}
            mandatory_fields.discard("city")
        return mandatory_fields
