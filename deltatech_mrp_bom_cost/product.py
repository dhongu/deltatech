# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
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



from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging
from openerp.osv.fields import related

from openerp.addons.product import _common

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'


    @api.multi
    def write(self, vals):
        res = super(ProductTemplate,self).write(vals)
        for template in self:
            if 'standard_price' in vals and template.product_variant_count == 1:
                product = template.product_variant_ids[0]
                if vals['standard_price'] <> product.standard_price:
                    product.write({'standard_price':vals['standard_price']})          
        return res

    
 
class ProductProduct(models.Model):
    _inherit = 'product.product'
    
    bom_price = fields.Float(digits= dp.get_precision('Account'), string='BOM Price', compute='_calculate_bom_price')
    standard_price = fields.Float()

    @api.one
    def _calculate_bom_price(self ):
        bom_id = self.env['mrp.bom']._bom_find( product_id = self.id)
        if bom_id:
            bom = self.env['mrp.bom'].browse(bom_id)
            self.bom_price = bom.calculate_price
        else:
            self.bom_price = self.standard_price or self.product_tmpl_id.standard_price
        
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: