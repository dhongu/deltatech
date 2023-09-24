# ©  2020 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def create_rule(self):
        for record in self:
            rules = record.env["stock.warehouse.orderpoint"].search([("product_id", "=", record.id)])
            if not rules and record.type == "product":
                record.env["stock.warehouse.orderpoint"].create(
                    {"product_id": record.id, "product_min_qty": 0, "product_max_qty": 0, "qty_multiple": 0}
                )

    @api.model
    def create(self, vals):
        product = super(ProductProduct, self).create(vals)
        product.create_rule()
        return product
