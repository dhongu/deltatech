# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import _, http
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

    def _get_carrier_city_domain(self, order_sudo, state, address_type="billing", use_delivery_as_billing=False):
        """Restrict the offered localities to the catalog of the chosen carrier.

        Only the delivery address is concerned: where the parcel is billed is
        no business of the courier. The restriction is skipped when no carrier
        is selected yet, when the carrier has no locality catalog of its own,
        or when its catalog holds no locality at all in that state (catalog not
        imported yet, or state not covered by the carrier) - otherwise the
        customer would be left with an empty list.
        """
        if address_type != "delivery" and not use_delivery_as_billing:
            return []
        carrier = order_sudo.carrier_id if order_sudo else None
        if not carrier or not state:
            return []
        domain = carrier.sudo()._get_city_domain() if hasattr(carrier, "_get_city_domain") else []
        if not domain:
            return []
        known_cities = request.env["res.city"].sudo().search_count([("state_id", "=", state.id)] + domain, limit=1)
        return domain if known_cities else []

    def _validate_address_values(self, address_values, partner_sudo, address_type, *args, **kwargs):
        invalid_fields, missing_fields, error_messages = super()._validate_address_values(
            address_values, partner_sudo, address_type, *args, **kwargs
        )
        city_id = address_values.get("city_id")
        if city_id:
            city = request.env["res.city"].sudo().browse(int(city_id))
            city_domain = self._get_carrier_city_domain(
                request.website.sale_get_order(),
                city.state_id,
                address_type=address_type,
                use_delivery_as_billing=args[0] if args else kwargs.get("use_delivery_as_billing", False),
            )
            if city_domain and not city.filtered_domain(city_domain):
                invalid_fields.add("city_id")
                error_messages.append(_("The selected city is not served by the chosen delivery method."))
        return invalid_fields, missing_fields, error_messages

    def _prepare_address_form_values(self, order_sudo, partner_sudo, *args, **kwargs):
        rendering_values = super()._prepare_address_form_values(order_sudo, partner_sudo, *args, **kwargs)
        state = request.env["res.country.state"].browse(rendering_values["state_id"])
        city = partner_sudo.city_id
        ResCity = request.env["res.city"].sudo()
        city_domain = self._get_carrier_city_domain(
            order_sudo,
            state,
            address_type=rendering_values.get("address_type", "billing"),
            use_delivery_as_billing=kwargs.get("use_delivery_as_billing", False),
        )

        rendering_values.update(
            {
                "state": state,
                "state_cities": ResCity.search([("state_id", "=", state.id)] + city_domain) if state else ResCity,
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
    def state_infos(self, state, address_type="billing", use_delivery_as_billing=False, **kw):
        order_sudo = request.website.sale_get_order()
        city_domain = self._get_carrier_city_domain(
            order_sudo,
            state,
            address_type=address_type,
            use_delivery_as_billing=use_delivery_as_billing in (True, "True", "true", "1"),
        )
        return dict(
            cities=[(st.id, st.display_name, st.zipcode or "") for st in state.get_website_sale_cities(city_domain)],
        )
