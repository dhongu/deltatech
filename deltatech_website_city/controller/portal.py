# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request

from odoo.addons.portal.controllers.portal import CustomerPortal


class CustomerPortalCity(CustomerPortal):
    MANDATORY_BILLING_FIELDS = ["name", "phone", "email", "street", "city", "country_id"]
    OPTIONAL_BILLING_FIELDS = ["zipcode", "state_id", "vat", "company_name", "city_id"]

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortalCity, self)._prepare_portal_layout_values()
        values["city_id"] = request.env.user.partner_id.city_id.id
        return values

    @http.route(
        ['/shop/state_infos/<model("res.country.state"):state>'],
        type="json",
        auth="public",
        methods=["POST"],
        website=True,
    )
    def state_infos(self, state, **kw):
        return dict(
            cities=[(st.id, st.name, st.zipcode or "") for st in state.get_website_sale_cities()],
        )
