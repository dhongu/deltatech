# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import http
from odoo.http import request

from odoo.addons.website_sale.controllers import main


class WebsiteSale(main.WebsiteSale):
    @http.route(["/shop/get_attribute_values"], type="json", auth="public", website=True)
    def get_attribute_values(self, attribute_id, attribute_value_ids=None, **kw):
        attribute = request.env["product.attribute"].sudo().browse(int(attribute_id))
        values = attribute.get_attribute_values(attribute_value_ids)
        return values
