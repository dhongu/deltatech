# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, models
from odoo.http import request
from odoo.tools import safe_eval


class Website(models.Model):
    _inherit = "website"

    @api.multi
    def sale_product_domain(self):
        domain = super(Website, self).sale_product_domain()
        search = request.params.get("search", False)
        if search:
            get_param = self.env["ir.config_parameter"].sudo().get_param
            catalog_search = safe_eval(get_param("alternative.search_catalog", "False"))
            alternative_limit = safe_eval(get_param("alternative.alternative_limit", "10"))

            product_ids = []
            alt_domain = [("name", "ilike", search)]

            if catalog_search:
                prods = self.env["product.product"].search_in_catalog(search)
                product_ids += prods.mapped("product_tmpl_id").mapped("id")

            alternative_ids = self.env["product.alternative"].search(alt_domain, limit=alternative_limit)
            for alternative in alternative_ids:
                product_ids += [alternative.product_tmpl_id.id]
            if product_ids:
                if len(product_ids) == 1:
                    domain += ["|", ("id", "=", product_ids[0])]
                else:
                    domain += ["|", ("id", "in", product_ids)]

        return domain
