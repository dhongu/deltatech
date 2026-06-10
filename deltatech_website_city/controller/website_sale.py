# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleCity(WebsiteSale):
    def _get_mandatory_billing_address_fields(self, country_sudo):
        mandatory_fields = super()._get_mandatory_billing_address_fields(country_sudo)
        if country_sudo.enforce_cities:
            mandatory_fields |= {
                "city_id",
                "state_id",
            }
            mandatory_fields.remove("city")
        return mandatory_fields

    def _get_mandatory_delivery_address_fields(self, country_sudo):
        mandatory_fields = super()._get_mandatory_delivery_address_fields(country_sudo)
        if country_sudo.enforce_cities:
            mandatory_fields |= {
                "city_id",
                "state_id",
            }
            mandatory_fields.remove("city")
        return mandatory_fields

    def _parse_form_data(self, form_data):
        city_id = form_data.get("city_id")
        if city_id:
            form_data["city"] = request.env["res.city"].sudo().browse(int(city_id)).name
        return super()._parse_form_data(form_data)

    def _prepare_address_form_values(self, order_sudo, partner_sudo, *args, **kwargs):
        rendering_values = super()._prepare_address_form_values(order_sudo, partner_sudo, *args, **kwargs)
        state = request.env["res.country.state"].browse(rendering_values["state_id"])
        city = partner_sudo.city_id
        ResCity = request.env["res.city"].sudo()

        rendering_values.update(
            {
                "state": state,
                "state_cities": ResCity.search([("state_id", "=", state.id)]) if state else ResCity,
                "city": city,
                "city_id": city.id if city else False,
            }
        )
        return rendering_values

    @http.route(
        ['/shop/state_infos/<model("res.country.state"):state>'],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def state_infos(self, state, **kw):
        return dict(
            cities=[(st.id, st.display_name, st.zipcode or "") for st in state.get_website_sale_cities()],
        )
