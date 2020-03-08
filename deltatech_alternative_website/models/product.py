# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, tools, _

from odoo.exceptions import Warning, RedirectWarning

import base64  # file encode
import codecs

from io import BytesIO

from PIL import Image
from PIL import ImageEnhance





class product_catalog(models.Model):
    _inherit = "product.catalog"

    public_categ_ids = fields.Many2many('product.public.category', string='Public Category',
                                        help="Those categories are used to group similar products for e-commerce.")

    @api.multi
    def create_product(self):
        products = super(product_catalog, self).create_product()
        for prod_cat in self:
            if prod_cat.public_categ_ids and prod_cat.product_id:
                prod_cat.product_id.public_categ_ids = prod_cat.public_categ_ids

        return products

