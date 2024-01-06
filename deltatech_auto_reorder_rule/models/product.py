# ©  2022 Terrabit
# See README.rst file on addons root folder for license details

from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def create_rule(self):
        product_variants = self.mapped("product_variant_ids")
        product_variants.create_rule()


class ProductProduct(models.Model):
    _inherit = "product.product"

    def create_rule(self):
        company_id = self.env.company
        warehouse_id = self.env["stock.warehouse"].search([("company_id", "=", company_id.id)], limit=1)
        location_id = warehouse_id.lot_stock_id
        for product in self:
            # daca tipul de produs este consumabil sau serviciu nu se creează regula
            if product.type != "product":
                continue

            # daca produsul nu se cumpăra nu se creează regula
            if not product.purchase_ok:
                continue

            domain = [("product_id", "=", product.id), ("company_id", "=", company_id.id)]
            rules = self.env["stock.warehouse.orderpoint"].search(domain)
            if not rules:
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

    @api.model_create_multi
    def create(self, vals_list):
        products = super().create(vals_list)
        products.create_rule()
        return products
