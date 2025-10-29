# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.http import request, route

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalCity(CustomerPortal):
    def _prepare_address_form_values(self, partner_sudo, *args, **kwargs):
        rendering_values = super()._prepare_address_form_values(partner_sudo, *args, **kwargs)

        # Align with l10n_pe structure: provide state, state_cities (filtered by state), and city
        state = request.env["res.country.state"].browse(rendering_values.get("state_id"))
        city = partner_sudo.city_id
        ResCity = request.env["res.city"].sudo()
        rendering_values.update(
            {
                "state": state,
                "state_cities": ResCity.search([("state_id", "=", state.id)]) if state else ResCity,
                "city": city,
            }
        )
        return rendering_values

    def _get_mandatory_address_fields(self, country_sudo):
        mandatory_fields = super()._get_mandatory_address_fields(country_sudo)
        if country_sudo.enforce_cities:
            # Use set operations and remove free-text city when enforcing cities
            mandatory_fields |= {"city_id", "state_id"}
            if "city" in mandatory_fields:
                mandatory_fields.remove("city")
        return mandatory_fields

    @route(
        '/portal/state_infos/<model("res.country.state"):state>',
        type="jsonrpc",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def state_infos(self, state, **kw):
        cities = request.env["res.city"].sudo().search([("state_id", "=", state.id)])
        # Return similar tuple structure as website_sale: (id, display_name, zipcode or "")
        return {"cities": [(c.id, c.display_name, c.zipcode or "") for c in cities]}
