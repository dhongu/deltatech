# Copyright 2015, 2017 Jairo Llopis <jairo.llopis@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSale(WebsiteSale):
    def _prepare_address_form_values(self, *args, **kwargs):
        result = super()._prepare_address_form_values(*args, **kwargs)
        result["country"] = result.get("country") or request.website.company_id.country_id
        return result
