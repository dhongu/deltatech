# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, models
from odoo.tools.safe_eval import safe_eval


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def _search_get_detail(self, website, order, options):
        values = super()._search_get_detail(website, order, options)

        get_param = self.env["ir.config_parameter"].sudo().get_param

        if safe_eval(get_param("deltatech_alternative_website.search_index", "False")):
            values["search_fields"] = ["search_index"]
            values["mapping"]["search_index"] = {"name": "search_index", "type": "text", "match": True}
        else:
            values["search_fields"] += ["alternative_ids.name"]
            values["mapping"]["alternative_ids.name"] = {"name": "alternative_ids.name", "type": "text", "match": True}
        return values
