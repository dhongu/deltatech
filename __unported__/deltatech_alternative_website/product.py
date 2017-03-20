# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
 
from odoo import models, fields, api,tools, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import   Warning, RedirectWarning

import base64  #file encode

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO
from PIL import Image
from PIL import ImageEnhance


def reduce_opacity(im, opacity):
    """Returns an image with reduced opacity."""
    assert opacity >= 0 and opacity <= 1
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    else:
        im = im.copy()
    alpha = im.split()[3]
    alpha = ImageEnhance.Brightness(alpha).enhance(opacity)
    im.putalpha(alpha)
    return im

def watermark(im, mark,  opacity=1):
    """Adds a watermark to an image."""
    if opacity < 1:
        mark = reduce_opacity(mark, opacity)
    if im.mode != 'RGBA':
        im = im.convert('RGBA')
    # create a transparent layer the size of the image and draw the
    # watermark in that layer.
    layer = Image.new('RGBA', im.size, (0,0,0,0))
 
    # scale, but preserve the aspect ratio
    ratio = min(
        float(im.size[0]) / mark.size[0], float(im.size[1]) / mark.size[1])
    w = int(mark.size[0] * ratio)
    h = int(mark.size[1] * ratio)
    mark = mark.resize((w, h))
    layer.paste(mark, ((im.size[0] - w) / 2, (im.size[1] - h) / 2))
 
    # composite the watermark with the layer
    return Image.composite(layer, im, layer)


class product_template(models.Model):
    _inherit = "product.template"
    
    watermark_image = fields.Binary(string="Watermark image", compute="_get_watermark_image")
 
    
    
    @api.multi
    @api.depends('image')
    def _get_watermark_image(self):
        for product in self:
            if self.env.user.company_id.watermark_image and product.image:
                image_base64 = product.with_context(bin_size=False).read( ['image'] )[0]
                 
                img = image_base64.get('image')
                image_stream = StringIO.StringIO(img.decode('base64'))
                image = Image.open(image_stream)
                
                image_base64 = self.env.user.company_id.with_context(bin_size=False).read( ['watermark_image'] )[0]
                 
                img = image_base64.get('watermark_image')
                mark_stream = StringIO.StringIO(img.decode('base64'))
                mark_image = Image.open(mark_stream)
                watermark_image =  watermark(image, mark_image,  0.2)
                
                background_stream = StringIO.StringIO()
                watermark_image.save(background_stream, 'PNG')
                product.watermark_image = background_stream.getvalue().encode('base64')               
            else:
                product.watermark_image = product.image


class product_catalog(models.Model):
    _inherit = "product.catalog"

    public_categ_ids = fields.Many2many('product.public.category', string='Public Category', 
                                        help="Those categories are used to group similar products for e-commerce.")



    @api.multi
    def create_product(self):
        products = super(product_catalog,self).create_product()
        for prod_cat in self:
            if prod_cat.public_categ_ids and prod_cat.product_id:
                prod_cat.product_id.public_categ_ids = prod_cat.public_categ_ids
            
        return products
            

 
   


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: