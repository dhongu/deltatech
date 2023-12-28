# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    qty_multiple = fields.Float(
        "Qty Multiple",
        digits="Product Unit of Measure",
        default=1,
        compute="_compute_qty_multiple",
        inverse="_inverse_qty_multiple",
        store=True,
        help="The sale quantity will be rounded up to this multiple.  If it is 0, the exact quantity will be used.",
    )
    qty_minim = fields.Float(
        "Qty Minim",
        digits="Product Unit of Measure",
        default=1,
        compute="_compute_qty_multiple",
        inverse="_inverse_qty_minim",
        store=True,
        help="The minim sale quantity will.  If it is 0, the exact quantity will be used.",
    )

    @api.depends("product_variant_ids", "product_variant_ids.qty_multiple")
    def _compute_qty_multiple(self):
        unique_variants = self.filtered(lambda template: len(template.product_variant_ids) == 1)
        for template in unique_variants:
            template.qty_multiple = template.product_variant_ids.qty_multiple
            template.qty_minim = template.product_variant_ids.qty_minim
        for template in self - unique_variants:
            template.qty_multiple = "-1"
            template.qty_minim = "-1"

    def _inverse_qty_multiple(self):
        for product in self:
            if len(product.product_variant_ids) == 1:
                product.product_variant_ids.qty_multiple = product.qty_multiple

    def _inverse_qty_minim(self):
        for product in self:
            if len(product.product_variant_ids) == 1:
                product.product_variant_ids.qty_minim = product.qty_minim


class ProductProduct(models.Model):
    _inherit = "product.product"

    qty_multiple = fields.Float(
        "Qty Multiple",
        digits="Product Unit of Measure",
        default=1,
        help="The sale quantity will be rounded up to this multiple.  If it is 0, the exact quantity will be used.",
    )
    qty_minim = fields.Float("Qty Minim", digits="Product Unit of Measure", default=1, help="The minim sale quantity. ")
