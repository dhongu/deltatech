# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    # @api.model
    # def _search_get_detail(self, website, order, options):
    #     values = super(ProductTemplate, self)._search_get_detail(website, order, options)
    #     values["search_fields"] += ["alternative_ids.name"]
    #     return values
