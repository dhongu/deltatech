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
 
_logger = logging.getLogger(__name__)


# primary - e utilizat doar pentru calculul cantitatii primare
# normal   - elementele din kitul de baza
# optional - elemente optionale
# service - alte servicii prestate pentru lucrare 

ITEM_CATEG = [('primary','Primary'),('normal','Normal'),('optional','Optional'),('service','Service'),('opt_serv','Optional Service')]

class sale_order(models.Model):
    _inherit = 'sale.order'


    specification = fields.Boolean(string='Specification', default=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},)
    #articole de deviz
    article_ids = fields.One2many('sale.mrp.article','order_id', string="Articles", copy=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    
    
    #bom_id      =  fields.Many2one('mrp.bom', string='Kit')   eventual sa definesc acest kit de structura ?
    # se va folosi pentru insumarea componentelor principale
    qty_primary = fields.Float(string='Primary Quantity', readonly=True, digits=dp.get_precision('Product Unit of Measure'),
                                compute='_compute_qty_primary', store=True)  
    primary_uom = fields.Many2one('product.uom', string='Unit of Measure', readonly=True , 
                                  compute='_compute_qty_primary', store=True)  
    price_unit =  fields.Float(string='Unit Price', digits= dp.get_precision('Product Price'),
                               compute='_compute_price_unit', store=True)  
    
    #extrase de resurse
    resource_ids = fields.One2many('sale.mrp.resource','order_id',  string="Resources", copy=False, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )  


    #attributes = fields.One2many( comodel_name='sale.mrp.order.attribute', inverse_name='order_id',
    #                                      string='Order attributes', copy=True )

    @api.multi
    @api.depends('article_ids')
    def _compute_qty_primary(self):
        for order in self:
            order.qty_primary = 0
            for article in order.article_ids:
                if article.item_categ == 'primary':
                    order.qty_primary += article.product_uom_qty
                    order.primary_uom = article.product_uom


    @api.multi
    @api.depends('qty_primary','resource_ids')
    def _compute_price_unit(self):
        for order in self:
            amount = 0
            for resource in order.resource_ids:
                amount += resource.amount
            if  order.qty_primary <> 0:
                order.price_unit = amount / order.qty_primary

    @api.multi
    def button_update(self):
        self.ensure_one()
        self.order_line.write({'product_uom_qty':0.0})
  
        for resource in self.resource_ids:
            if resource.item_categ =='primary':
                continue
            line_to_update = self.env['sale.order.line']
            for line in self.order_line:
                if line.product_id.id == resource.product_id.id and line.item_categ == resource.item_categ:
                    line_to_update = line
                    break
       
            if not line_to_update: 
                vals = {'order_id':self.id,
                    'product_template':resource.product_id.product_tmpl_id.id,
                    'product_id':resource.product_id.id,
                    'name':resource.name,
                    'product_uom_qty':resource.product_uom_qty,
                    'price_unit':resource.price_unit,
                    'item_categ':resource.item_categ,
                    'product_uom':resource.product_uom.id} 
                
                fpos = self.fiscal_position
                if not fpos:
                    fpos = self.partner_id.property_account_position
                
                vals['tax_id'] = [[6,0,fpos.map_tax(resource.product_id.product_tmpl_id.taxes_id).ids]]     
                self.env['sale.order.line'].create(vals)

            else:
                qty = line_to_update.product_uom_qty + resource.product_uom_qty
                line_to_update.write({'name':resource.name,
                                      'product_uom_qty':qty,
                                      'price_unit':resource.price_unit})
        for line in self.order_line:
            if line.product_uom_qty == 0:
                line.unlink()

    @api.multi
    def button_dummy(self):
        res =  super(sale_order,self).button_dummy()
        for order in self:
            if order.specification:
                order.button_update()
        return res
    
    @api.multi
    def write(self,vals):
        res =  super(sale_order,self).write(vals)
        self.button_dummy()
        return res

"""
class sale_mrp_order_attribute(models.Model):
    _name = 'sale.mrp.order.attribute'

    order_id  = fields.Many2one('sale.oder', string='Sale Order', copy=False, ondelete='cascade')
    attribute = fields.Many2one( comodel_name='product.attribute', string='Attribute')
   
    value = fields.Many2one( comodel_name='product.attribute.value', string='Value',
                             domain="[('id', 'in', possible_values[0][2])]")
    possible_values = fields.Many2many( comodel_name='product.attribute.value',
                                        compute='_get_possible_attribute_values', readonly=True)

    @api.one
    @api.depends('attribute')
    def _get_possible_attribute_values(self):
        attr_values = self.env['product.attribute.value']
        attr_values = self.attribute.value_ids.ids
        self.possible_values = attr_values.sorted()
"""


# mai adaug categoria de cost  unde o sa intre manopera de montare lambriu / gips 
# la cantitatea se calculeaza dupa un filtru iar 

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    
    item_categ = fields.Selection(ITEM_CATEG, default='normal', string='Item Category')
    
    
 
 
class sale_mrp_article_attribute(models.Model):
    _name = 'sale.mrp.article.attribute'

    article_id  = fields.Many2one('sale.mrp.article', string='Article', copy=False, ondelete='cascade')
    attribute = fields.Many2one( comodel_name='product.attribute', string='Attribute')
   
    value = fields.Many2one( comodel_name='product.attribute.value', string='Value',
                             domain="[('id', 'in', possible_values[0][2])]")
    possible_values = fields.Many2many( comodel_name='product.attribute.value',
                                        compute='_get_possible_attribute_values', readonly=True)

    @api.one
    @api.depends('attribute', 'article_id.product_template',
                 'article_id.product_template.attribute_line_ids')
    def _get_possible_attribute_values(self):
        attr_values = self.env['product.attribute.value']
        template = self.article_id.product_template
        for attr_line in template.attribute_line_ids:
            if attr_line.attribute_id.id == self.attribute.id:
                attr_values |= attr_line.value_ids
        self.possible_values = attr_values.sorted()


   
class sale_mrp_article(models.Model):
    _name = 'sale.mrp.article'
    #_inherits = {'sale.order.line':'order_line_id'}
 
    _description = "Sale Article"
    _order = "sequence,id"
     
    order_id  = fields.Many2one('sale.order', string='Order', copy=False, ondelete='cascade',  required=True)
    #order_line_id = fields.Many2one('sale.order.line', string='Order Line Reference', ondelete="cascade",  required=True)
  
    sequence = fields.Integer(string='Sequence', default=10,   help="Gives the sequence of this line when displaying the order.")

    bom_id      =  fields.Many2one('mrp.bom', string='Norm')  # norma de deviz
    
    product_template = fields.Many2one('product.template', string='Product Template' )
    
    product_attributes = fields.One2many( comodel_name='sale.mrp.article.attribute', inverse_name='article_id',
                                          string='Product attributes', copy=True )
    product_attributes_count = fields.Integer( compute="_get_product_attributes_count")
    product_attributes_values = fields.Many2many( comodel_name='product.attribute.value',
                                        compute='_get_attribute_values', readonly=True)
    
    product_id  = fields.Many2one('product.product', string='Product Variant')
    name = fields.Char(string='Name')
    product_uom_qty = fields.Float(string='Product Quantity', required=True, digits=dp.get_precision('Product Unit of Measure'))
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    
    item_categ = fields.Selection(ITEM_CATEG, default='optional', string='Item Category')
    
    #primary_item = fields.Boolean(string='Primary Item')
    #category_id = fields.Many2one('sale.mrp.article.category', string='Article Category')
    
    price_unit =  fields.Float(string='Unit Price', digits= dp.get_precision('Product Price'),compute='_compute_amount',  )
    resource_ids = fields.One2many('sale.mrp.resource',inverse_name='article_id', string="Resources", copy=True)
    amount      = fields.Float( string='Subtotal', digits= dp.get_precision('Account'), compute='_compute_amount', store=True)   

    #article_property_ids = fields.Many2many('mrp.property', string='Properties', compute='_compute_properties'  , inverse='_inverse_properties', readonly=False)
  
    #property_ids = fields.Many2many('mrp.property', 'sale_order_article_property_rel', 'article_id', 'property_id', 'Properties')


    @api.one
    @api.depends('product_attributes')
    def _get_attribute_values(self):
        attr_values = self.env['product.attribute.value']
        for attr_line in self.product_attributes:
            attr_values |= attr_line.value
        self.product_attributes_values = attr_values.sorted()
 
    @api.one
    @api.depends('product_attributes')
    def _get_product_attributes_count(self):
        self.product_attributes_count = len(self.product_attributes)

    @api.multi
    @api.depends('resource_ids')
    def _compute_amount(self):
        for article in self:
            article.amount = 0
            for resource in article.resource_ids:
                article.amount +=  resource.amount
            if article.product_uom_qty:
                article.price_unit = article.amount / article.product_uom_qty
    
    @api.one
    @api.onchange('bom_id')
    def onchange_bom(self):
        if self.bom_id:
            self.product_template = self.bom_id.product_tmpl_id
            self.item_categ = 'normal'
            if self.bom_id.product_id:
                self.product_id = self.bom_id.product_id
        self.explode_bom()
         

             

    @api.one
    @api.onchange('product_template')
    def onchange_product_template(self):
        self.ensure_one()
        self.name = self.product_template.name
        if not self.product_template.attribute_line_ids:
            self.product_id = ( self.product_template.product_variant_ids and
                                self.product_template.product_variant_ids[0])
        else:
            self.product_id = False
            self.product_uom = self.product_template.uom_id
        
        attributes =  (self.product_template._get_product_attributes_dict())
        
        self.product_attributes = attributes
        for attribute in self.product_attributes:
            if not attribute.value:
                if attribute.attribute.default_value:
                    attribute.value = attribute.attribute.default_value

        bom_id = self.env['mrp.bom']._bom_find(product_tmpl_id = self.product_template.id)
        bom = self.env['mrp.bom'].browse(bom_id)
        if bom.type == 'phantom':
            self.bom_id = bom
 
         



    @api.one
    @api.onchange('product_attributes')
    def onchange_product_attributes(self):
        product_obj = self.env['product.product']
        self.product_id = product_obj._product_find(self.product_template,
                                                    self.product_attributes)
        self.explode_bom()
        

        
    @api.one
    @api.onchange('product_id' )
    def onchange_product_id(self):

        if not self.product_id:
            return
        
        
        self.name  = self.product_id.with_context(context=self.order_id.partner_id).name_get()[0][1]
        #if self.product_id.description_sale:
        #    self.name += '\n'+self.product_id.description_sale 

        if self.product_id.type  == 'service':
            self.item_categ = 'service'
            
                               
        bom_id = self.env['mrp.bom']._bom_find(product_tmpl_id = self.product_template.id,
                                               product_id      = self.product_id.id,
                                               )
        if bom_id:
            bom = self.env['mrp.bom'].browse(bom_id)
            if bom.type == 'phantom':
                self.bom_id = bom
 
        self.product_uom = self.product_id.uom_id
        attributes = (self.product_id._get_product_attributes_values_dict())
       
        self.product_attributes = attributes

 



 
    @api.onchange('product_uom_qty','item_categ')
    def onchange_product_uom_qty(self):
        self.explode_bom() 
       


    @api.model
    def explode_bom(self):
       
        article = self
        items = []
        if self.bom_id:
            factor = self.env['product.uom']._compute_qty(self.product_uom.id, self.product_uom_qty, self.bom_id.product_uom.id)
            
        
            factor =  factor / self.bom_id.product_qty
             
            items, work = self.bom_id.with_context(production=self)._bom_explode(product=self.product_id, factor = factor)
            """         
            items  = self.bom_id._bom_explode_variants_categ( 
                                                          product=self.product_id, 
                                                          factor = factor, 
                                                          product_attributes = self.product_attributes,
                                                          )
            """
            #print routing, items 
        else:
            if self.product_id:
                items =  [{ 'product_template':self.product_template.id,
                            'product_id': self.product_id and self.product_id.id,
                            'product_qty': self.product_uom_qty,
                            'product_uom': self.product_uom.id,
                            'item_categ':self.item_categ
                           }] 
         
        
        resources = []
        for item in items:
            product = self.env['product.product'].browse(item['product_id'])
            if product:    # and item['product_qty'] <> 0:
                
                if self.order_id.pricelist_id:
                    price_list_id = self.order_id.pricelist_id.id
             
                    price_unit = self.order_id.pricelist_id.price_get( item['product_id'], item['product_qty'] or 1.0, self.order_id.partner_id.id)[price_list_id]
                    price_unit = self.env['product.uom']._compute_price(product.uom_id.id, price_unit, item['product_uom'] )
                else:
                    price_unit = 0
                        
                value = {           'product_template':item['product_template'],
                                    'product_id': item['product_id'],
                                    'product_uom_qty': item['product_qty'],
                                    'product_uom': item['product_uom'],
                                    'price_unit': price_unit,
                                    'amount': price_unit * item['product_qty'],
                                    'state':'draft',
                                    'item_categ':item['item_categ'],
                                    }
        
                value['name'] = product.with_context(context=self.order_id.partner_id).name_get()[0][1]
                #if product.description_sale:
                #     value['name'] += '\n'+product.description_sale 
 
                #value['order_id'] = self.order_id.id
                #value['article_id'] = self.id
                    
                resources += [(0,0,value)]
                #resources += [value]
        
         
        resource_ids =  self._convert_to_cache({'resource_ids': resources }, validate=False)
         
        self.update(resource_ids) 
        for resource in self.resource_ids:
            resource.onchange_product_id()
            
        #self.resource_ids = (resources)
        return resource_ids
        #article.order_id.resource_ids.invalidate_cache()            
      
class sale_mrp_resource(models.Model):
    _name = 'sale.mrp.resource'
    #_inherits = {'sale.order.line':'order_line_id'}
    
    _description = "Sale Resource"
     
    order_id  = fields.Many2one('sale.order', related='article_id.order_id', store=True, string='Order', copy=False)
    #order_line_id = fields.Many2one('sale.order.line', string='Order Line Reference', ondelete="cascade",  required=True)

    article_id  = fields.Many2one('sale.mrp.article', string='Article', copy=False, ondelete='cascade')
    
    item_categ = fields.Selection(ITEM_CATEG, default='normal', string='Item Category')

    product_id  = fields.Many2one('product.product', string='Product')
    name        = fields.Char(string='Name')
    product_uom_qty = fields.Float(string='Product Quantity', required=True, digits =dp.get_precision('Product Unit of Measure'))
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=True)
    price_unit  = fields.Float(string='Unit Price', digits = dp.get_precision('Product Price') )
    amount      = fields.Float( string='Subtotal', digits = dp.get_precision('Account'), compute='_compute_amount', store=True)   
    categ_id    = fields.Many2one('product.category', related='product_id.categ_id', store=True) # este nevoie ? mai bine se aduce informatia direct in raport ?



    @api.multi
    @api.depends('price_unit','product_uom_qty')
    def _compute_amount(self):
        for resource in self:
            resource.amount = resource.product_uom_qty * resource.price_unit





    @api.onchange('product_id','product_uom_qty')
    def onchange_product_id(self):
        if self.product_id and self.article_id.order_id and self.article_id.order_id.pricelist_id:
           
            self.product_uom = self.product_id.uom_id
            order_id = self.article_id.order_id
            
            bom_id = self.env['mrp.bom']._bom_find( product_id   = self.product_id.id )
            if bom_id:
                bom = self.env['mrp.bom'].browse(bom_id)
                price = bom.with_context(production=self.article_id).get_price(order_id.partner_id,order_id.pricelist_id)
            else:
                price =  order_id.pricelist_id.price_get( self.product_id.id, self.product_uom_qty or 1.0,  order_id.partner_id.id)[ order_id.pricelist_id.id]
                
            price = self.env['product.uom']._compute_price(self.product_id.uom_id.id, price, self.product_uom.id ) # nu cred ca e cazul ca sa mai schimb si unitatea de masura 
            self.price_unit = price
            self.name = self.product_id.name
            #result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            #if self.product_id.description_sale:
            #    self.name += '\n'+self.product_id.description_sale 
                
       
    