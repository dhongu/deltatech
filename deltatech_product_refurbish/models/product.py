# ©  2015-2020 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    has_refurbish = fields.Boolean(compute="_compute_refurbish")
    refurbish_ids = fields.Many2many("stock.production.lot", compute="_compute_refurbish")

    def _compute_refurbish(self):
        domain_loc = self.env["product.product"].sudo()._get_domain_locations()[0]

        for product in self:
            refurbish_ids = self.env["stock.production.lot"]
            domain = domain_loc + [("product_id", "in", product.product_variant_ids.ids)]
            quants = self.env["stock.quant"].sudo().search(domain)
            for quant in quants:
                if quant.lot_id.condition == "refurbish" and not quant.reserved_quantity:
                    refurbish_ids |= quant.lot_id
            product.refurbish_ids = refurbish_ids
            product.has_refurbish = bool(refurbish_ids)

    def _get_combination_info(
        self,
        combination=False,
        product_id=False,
        add_qty=1,
        pricelist=False,
        parent_combination=False,
        only_template=False,
    ):

        combination_info = super(ProductTemplate, self)._get_combination_info(
            combination=combination,
            product_id=product_id,
            add_qty=add_qty,
            pricelist=pricelist,
            parent_combination=parent_combination,
            only_template=only_template,
        )

        if not self.env.context.get("website_sale_stock_get_quantity"):
            return combination_info

        if self.has_refurbish:
            combination_info["virtual_available"] -= len(self.refurbish_ids)

        return combination_info
