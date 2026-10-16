# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    pallet_product_id = fields.Many2one("product.product")
    pallet_qty_min = fields.Float(digits="Product Unit of Measure")  # cantitatea minima pe palet
    pallet_price = fields.Float("Pallet Price", default=1.0, digits="Product Price", compute="_compute_pallet_price")

    @api.depends("list_price", "pallet_qty_min", "pallet_product_id", "pallet_product_id.list_price")
    def _compute_pallet_price(self):
        for template in self:
            price = 0
            if template.pallet_product_id:
                price = template.pallet_product_id.list_price
            if template.pallet_qty_min:
                price = price + template.pallet_qty_min * template.list_price
            template.pallet_price = price
