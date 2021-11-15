# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ProductPricelistItem(models.Model):
    _inherit = "product.pricelist.item"

    price_text = fields.Char(string="Text Price", readonly=True, compute="_compute_text_price")

    @api.depends("base", "price_discount", "price_surcharge")
    def _compute_text_price(self):
        # todo: de convertit in format local
        for item in self:
            value = 1 + item.price_discount

            item.price_text = item._price_field_get()[item.base - 1][1] + " * " + str(value)
            if item.price_surcharge:
                item.price_text += str(item.price_surcharge)
