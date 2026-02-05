# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1.0,
        uom_id=False,
        only_template=False,
    ):
        combination_info = super()._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            uom_id=uom_id,
            only_template=only_template,
        )
        taxes = combination_info.get("taxes", self.taxes_id)
        res = taxes.compute_all(combination_info["list_price"], product=self)
        excluded = res["total_excluded"]
        combination_info["list_price_without_tax"] = excluded

        return combination_info
