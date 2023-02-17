# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.http import request
from odoo.osv import expression

from odoo.addons.website_sale.controllers import main

#  FH312316, dc35407, CC106785

# metodele pentru dezactivarea fuzzy search sunt mutate in modulul deltatech_website_disable_fuzzy_search


class WebsiteSale(main.WebsiteSale):
    def _get_search_domain(self, search, category, attrib_values, search_in_description=True):
        domains = super(WebsiteSale, self)._get_search_domain(search, category, attrib_values, search_in_description)
        if search:
            alternative_ids = request.env["product.alternative"]
            for srch in search.split(" "):
                alt_domain = [("name", "ilike", srch)]
                alternative_ids |= request.env["product.alternative"].search(alt_domain, limit=10)
            product_tmpl_ids = alternative_ids.mapped("product_tmpl_id")

            if product_tmpl_ids:
                subdomains = [("id", "in", list(product_tmpl_ids.ids))]
                domains = expression.OR([subdomains, domains])

        return domains
