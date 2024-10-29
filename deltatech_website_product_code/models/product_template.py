# ©  2015-2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _search_render_results(self, fetch_fields, mapping, icon, limit):
        fetch_fields += ["default_code", "display_name"]

        results_data = super()._search_render_results(fetch_fields, mapping, icon, limit)

        for _product, data in zip(self, results_data, strict=False):
            if data.get("default_code"):
                data["name"] = "[{}] {}".format(data["default_code"], data["name"])

        return results_data
