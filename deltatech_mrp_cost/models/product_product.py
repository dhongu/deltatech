# © 2025 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _compute_bom_price(self, bom, boms_to_recompute=False, byproduct_bom=False):
        price =  super()._compute_bom_price(bom, boms_to_recompute=boms_to_recompute, byproduct_bom=byproduct_bom)
        costs = (
            bom.overhead_amount
            + bom.utility_consumption * bom.global_duration
            + bom.net_salary_rate * bom.global_duration
            + bom.salary_contributions * bom.global_duration
        )
        if costs:
            price += costs / bom.product_qty
        return price




