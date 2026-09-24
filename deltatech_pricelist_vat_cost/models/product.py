from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price_with_vat = fields.Float(
        string="Cost with VAT", readonly=True, compute="_compute_standard_price_with_vat"
    )

    @api.depends("standard_price", "taxes_id")
    def _compute_standard_price_with_vat(self):
        for product in self.sudo():
            if product.taxes_id and product.standard_price:
                taxes = product.supplier_taxes_id.compute_all(
                    product.standard_price, product.currency_id, 1, product=product, handle_price_include=False
                )
                product.standard_price_with_vat = taxes["total_included"]
            else:
                product.standard_price_with_vat = product.standard_price


class ProductProduct(models.Model):
    _inherit = "product.product"

    standard_price_with_vat = fields.Float(
        string="Cost with VAT", readonly=True, compute="_compute_standard_price_with_vat"
    )

    @api.depends("standard_price", "taxes_id")
    def _compute_standard_price_with_vat(self):
        for variant in self.sudo():
            if variant.taxes_id and variant.standard_price:
                taxes = variant.supplier_taxes_id.compute_all(
                    variant.standard_price, variant.currency_id, 1, product=variant, handle_price_include=False
                )
                variant.standard_price_with_vat = taxes["total_included"]
            else:
                variant.standard_price_with_vat = variant.standard_price
