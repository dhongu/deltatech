# Copyright 2015, 2017 Jairo Llopis <jairo.llopis@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    def _get_default_country(self, order_sudo=False, **kwargs):
        """Fall back on the country of the website's company: the address form then shows the
        states, the phone code and the required fields of that country."""
        return super()._get_default_country(order_sudo=order_sudo, **kwargs) or (self.env.website.company_id.country_id)

    def _prepare_address_form_values(self, *args, **kwargs):
        result = super()._prepare_address_form_values(*args, **kwargs)
        if not result.get("country"):
            # an existing address without a country: preselect the company's country too
            country = self.env.website.company_id.country_id
            result["country"] = country
            result["states"] = country.state_ids
        return result
