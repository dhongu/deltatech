# ©  2015-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale as Base


class WebsiteSale(Base):
    @route()
    def address(self, **kw):
        result = super(WebsiteSale, self).address(**kw)
        result.qcontext["country"] = result.qcontext.get("country") or request.website.company_id.country_id
        return result
