# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.http import request
from odoo.osv import expression

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleAlternative(WebsiteSale):
    def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
        domain = super(WebsiteSaleAlternative, self)._get_search_domain(
            search, category, attrib_values, search_in_description
        )
        if search:
            product_ids = []
            alt_domain = [("name", "ilike", search)]

            alternative_ids = request.env["product.alternative"].search(alt_domain, limit=10)
            for alternative in alternative_ids:
                product_ids += [alternative.product_tmpl_id.id]
            if product_ids:
                if len(product_ids) == 1:
                    subdomains = [("id", "=", product_ids[0])]
                    domain = expression.OR([subdomains, domain])
                else:
                    subdomains = [("id", "in", product_ids)]
                    domain = expression.OR([subdomains, domain])

        return domain
