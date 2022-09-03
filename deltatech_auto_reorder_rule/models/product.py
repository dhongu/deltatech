# ©  2020 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def create_rule(self):
        company_id = self.env.company
        warehouse_id = self.env["stock.warehouse"].search([("company_id", "=", company_id.id)], limit=1)
        location_id = warehouse_id.lot_stock_id
        for product in self:
            rules = self.env["stock.warehouse.orderpoint"].search(
                [("product_id", "=", product.id), ("company_id", "=", company_id.id)]
            )
            if not rules and product.type == "product":
                self.env["stock.warehouse.orderpoint"].create(
                    {
                        "product_id": product.id,
                        "product_min_qty": 0,
                        "product_max_qty": 0,
                        "qty_multiple": 0,
                        "company_id": company_id.id,
                        "name": product.name,
                        "warehouse_id": warehouse_id.id,
                        "location_id": location_id.id,
                    }
                )

    @api.model
    def create(self, vals):
        company_id = self.env.company
        warehouse_id = self.env["stock.warehouse"].search([("company_id", "=", company_id.id)], limit=1)
        location_id = warehouse_id.lot_stock_id
        prod_id = super(ProductProduct, self).create(vals)
        if prod_id.type == "product":
            self.env["stock.warehouse.orderpoint"].create(
                {
                    "product_id": prod_id.id,
                    "product_min_qty": 0,
                    "product_max_qty": 0,
                    "qty_multiple": 0,
                    "company_id": company_id.id,
                    "name": prod_id.name,
                    "warehouse_id": warehouse_id.id,
                    "location_id": location_id.id,
                }
            )
        return prod_id
