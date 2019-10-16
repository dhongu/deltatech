# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools, _
from odoo.exceptions import UserError, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.api import Environment


class product_pricelist_item(models.Model):
    _inherit = "product.pricelist.item"

    @api.one
    @api.depends('base', 'price_discount', 'price_surcharge')
    def _compute_text_price(self):
        # todo: de convertit in format local
        value = (1 + self.price_discount)

        self.price_text = self._price_field_get()[self.base - 1][1] + ' * ' + str(value)
        if self.price_surcharge:
            self.price_text += str(self.price_surcharge)

    price_text = fields.Char(string="Text Price", readonly=True, compute='_compute_text_price')
