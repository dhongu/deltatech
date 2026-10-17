from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    standard_price_with_vat = fields.Float(
        string="Cost with VAT", readonly=True, compute="_compute_standard_price_with_vat"
    )

    @api.depends(
        "standard_price",
        "currency_id",
        "supplier_taxes_id",
        "supplier_taxes_id.amount",
        "supplier_taxes_id.amount_type",
    )
    @api.depends_context("company")
    def _compute_standard_price_with_vat(self):
        company = self.env.company
        for product in self.sudo():
            taxes = product.supplier_taxes_id._filter_taxes_by_company(company)
            if taxes and product.standard_price:
                taxes = taxes.compute_all(
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

    @api.depends(
        "standard_price",
        "currency_id",
        "supplier_taxes_id",
        "supplier_taxes_id.amount",
        "supplier_taxes_id.amount_type",
    )
    @api.depends_context("company")
    def _compute_standard_price_with_vat(self):
        company = self.env.company
        for variant in self.sudo():
            taxes = variant.supplier_taxes_id._filter_taxes_by_company(company)
            if taxes and variant.standard_price:
                taxes = taxes.compute_all(
                    variant.standard_price, variant.currency_id, 1, product=variant, handle_price_include=False
                )
                variant.standard_price_with_vat = taxes["total_included"]
            else:
                variant.standard_price_with_vat = variant.standard_price
