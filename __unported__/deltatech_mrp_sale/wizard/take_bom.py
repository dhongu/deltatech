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



from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp


class take_bom(models.TransientModel):
    _name = 'sale.mrp.take.bom'
    _description = "Take BOM in Sale Order"
    
    product_id  =  fields.Many2one('product.product', string='Product Variant')
    bom_id      =  fields.Many2one('mrp.bom', string='Article List')


    @api.onchange('product_id')
    def onchange_product(self):
        bom_id = self.env['mrp.bom']._bom_find(product_id = self.product_id.id)
        self.bom_id = bom_id  # merge sa asignez un nr la un obiect?? Da:)

    @api.onchange('bom_id')
    def onchange_bom(self):
        if self.bom_id and self.bom_id.product_id:
            self.product_id = self.bom_id.product_id
    
    
    @api.multi
    def take(self):
        active_id = self.env.context.get('active_id', False)
        sale_order =  self.env['sale.order'].browse(active_id)
        
        if self.product_id: 
            sale_order.attributes = (self.product_id._get_product_attributes_values_dict())
            sale_order.client_order_ref = self.product_id.name
        else:
            sale_order.attributes =  (self.bom_id.product_tmpl_id._get_product_attributes_dict())
            sale_order.client_order_ref = self.bom_id.name       
        
        
         
        for item in self.bom_id.bom_line_ids:
            
            values = {  'order_id':active_id,
                         'product_template':item.product_template.id,
                         'product_id':item.product_id.id,
                         
                         'product_uom_qty':item.product_qty,
                         'product_uom':item.product_uom.id,
                         'item_categ':item.item_categ}
            
            bom_id = self.env['mrp.bom']._bom_find(product_tmpl_id = item.product_template.id,
                                                   product_id      = item.product_id.id )
            if bom_id:
                bom = self.env['mrp.bom'].browse(bom_id)
                if bom.type == 'phantom':
                    values['bom_id'] = bom_id            
            
            
            article = sale_order.article_ids.create(values)  
            
            attributes = article._get_attributes()
            for attribute in attributes:
                attribute['article_id'] = article.id
                article.product_attributes.create(attribute)
                
            article.explode_bom()
            


        


        
                     



            
        return True
        