# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.http import request
from odoo.osv import expression

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAttribute(WebsiteSale):
    def _get_search_domain(self, search, category, attrib_values, search_in_description=True):

        domain = super()._get_search_domain(
            search, category, attrib_values, search_in_description=search_in_description
        )

        if search and search_in_description:
            attribute_value_ids = request.env["product.attribute.value"].search([("name", "ilike", search)])
            if attribute_value_ids:
                prods = attribute_value_ids.mapped("pav_attribute_line_ids").mapped("product_tmpl_id")
                domain_matching = [("id", "in", prods.ids)]
                domain = expression.OR([domain, domain_matching])

        return domain
