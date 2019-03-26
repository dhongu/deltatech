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
from odoo.exceptions import except_orm, Warning, RedirectWarning, ValidationError
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging
from odoo.osv.fields import related
 
_logger = logging.getLogger(__name__)


# primary - e utilizat doar pentru calculul cantitatii primare
# normal   - elementele din kitul de baza
# optional - elemente optionale
# service - alte servicii prestate pentru lucrare 

ITEM_CATEG = [('primary','Primary'),
              ('normal','Normal'),
              ('optional','Optional'),
              ('service','Service'),
              ('labor', 'Labor'),
              ('opt_serv','Optional Service')]

class sale_order(models.Model):
    _inherit = 'sale.order'

    

    specification = fields.Boolean(string='Specification', default=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},)
    #articole de deviz
    article_ids = fields.One2many('sale.mrp.article','order_id', string="Articles", copy=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
    
    
    #bom_id      =  fields.Many2one('mrp.bom', string='Kit')   eventual sa definesc acest kit de structura ?
    # se va folosi pentru insumarea componentelor principale
    qty_primary = fields.Float(string='Primary Quantity', readonly=True, digits=dp.get_precision('Product Unit of Measure'),
                                compute='_compute_qty_primary', store=True)  
    primary_uom = fields.Many2one('uom.uom', string='Unit of Measure', readonly=True , 
                                  compute='_compute_qty_primary', store=True)  
    price_unit =  fields.Float(string='Unit Price', digits= dp.get_precision('Product Price'),
                               compute='_compute_price_unit', store=True)  
    
    #extrase de resurse
    resource_ids = fields.One2many('sale.mrp.resource','order_id',  string="Resources", copy=False, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )  
    resource_item_ids = fields.One2many('sale.mrp.resource.item', inverse_name='order_id', string="All Products", copy=True)

    attributes = fields.One2many( comodel_name='sale.mrp.order.attribute', inverse_name='order_id',
                                          string='Order attributes', copy=True, readonly=True, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]} )
     
    add_inst_day = fields.Integer(string="Additional installing days")


    
    
    @api.multi
    @api.depends('article_ids.product_uom_qty')
    def _compute_qty_primary(self):
        for order in self:
            order.qty_primary = 0
            for article in order.article_ids:
                if article.item_categ == 'primary':
                    order.qty_primary += article.product_uom_qty
                    order.primary_uom = article.product_uom
            order.add_inst_day = order.qty_primary / 4


    @api.multi
    @api.depends('qty_primary','resource_ids')
    def _compute_price_unit(self):
        for order in self:
            amount = 0
            for resource in order.resource_ids:
                amount += resource.amount
            if  order.qty_primary != 0:
                order.price_unit = amount / order.qty_primary


    @api.multi
    def button_update_all(self):
        for order in self:
            order.resource_item_ids.unlink()    
            for resource in order.resource_ids:
                if resource.product_uom_qty != 0.0:
                    resource.explode_bom()    

    @api.multi
    def button_update(self):

        self.ensure_one()
        self.order_line.write({'product_uom_qty':0.0})
  
        for resource in self.resource_ids:

            line_to_update = self.env['sale.order.line']
            for line in self.order_line:
                if line.product_id.id == resource.product_id.id and line.item_categ == resource.item_categ and resource.product_uom.name != '%':
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
                    'product_uom':resource.product_uom.id,
                    'sequence':resource.article_id.sequence} 
                
                fpos = self.fiscal_position
                if not fpos:
                    fpos = self.partner_id.property_account_position
                
                vals['tax_id'] = [[6,0,fpos.map_tax(resource.product_id.product_tmpl_id.taxes_id).ids]]     
                self.env['sale.order.line'].create(vals)

            else:
                qty = line_to_update.product_uom_qty + resource.product_uom_qty
                line_to_update.write({'name':resource.name,
                                      'product_uom_qty':qty,
                                      'sequence':resource.article_id.sequence,
                                      'price_unit':resource.price_unit})
        for line in self.order_line:
            if line.product_uom_qty == 0:
                line.unlink()

        #super(sale_order,self).button_update()
        
        for article in self.article_ids:
            if article.product_uom.name == '%':
                for line in self.order_line:
                    if article.product_id == line.product_id:
                        article.write({'price_unit':line.price_unit,
                                       'amount':line.price_subtotal})
        
        article_to_update = self.env['sale.mrp.article']
        """
        for resource in self.resource_ids:
            if resource.product_uom.name == '%':
                for line in self.order_line:
                    if resource.product_id == line.product_id:
                        resource.write({'price_unit':line.price_unit,
                                       'amount':line.price_subtotal})
                        
                        # na ca acum trebuie sa actulizez si pretul articolului
                        article_to_update |= resource.article_id
        """
        # daca am unitatea de masura procent in resursa atunci valoarea se caluleaza din celelelta pozitii ale articolului
        for resource in self.resource_ids:
            if resource.product_uom.name == '%':
                article_to_update |= resource.article_id
                domain  = eval( resource.product_id.percent_domain )
                domain.extend([('article_id','=',resource.article_id.id),('id','!=',resource.id)])
                resource_lines = self.env['sale.mrp.resource'].search(domain)
                total_amount = 0
                for line in resource_lines:
                    total_amount += line.amount
                total_amount =  total_amount / 100 
                
                resource.write({'price_unit':total_amount,
                                       'amount':total_amount * resource.product_uom_qty })
        
        for article in article_to_update:
            amount = 0
            for resource in article.resource_ids:
                amount +=  resource.amount
            if article.product_uom_qty:
                price_unit = article.amount / article.product_uom_qty
                
            article.write({'price_unit':price_unit, 'amount':amount})                       
                                          
        self.button_update_all()

    # actualizarea liniilor din comanda se face manula prin apasarea unui buton
    """
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



    @api.multi
    def button_update_order_attribute(self):
        for order in self:       
            # transfer atribute de la produs in lista de atribute a comenzii
            order_attribute_values = {}
            
            for order_attr in order.attributes:
                order_attribute_values[order_attr.attribute.id] = order_attr.value.id
                
            for article in order.article_ids: 
                for attribute in article.product_attributes:
                    if attribute.value:
                        order_attribute_values[attribute.attribute.id] = attribute.value.id
           
            order_attribute = self.env['sale.mrp.order.attribute'] 
            for key, value in order_attribute_values.items():
                order_attribute += self.env['sale.mrp.order.attribute'].new({ 'attribute':key, 'value':value}) 
            order.attributes = order_attribute
        
 


class sale_mrp_order_attribute(models.Model):
    _name = 'sale.mrp.order.attribute'

    _order = 'sequence'
    sequence = fields.Integer(string='Sequence', related="attribute.sequence", store=True)


    order_id  = fields.Many2one('sale.order', string='Sale Order', copy=False, ondelete='cascade')
    attribute = fields.Many2one( comodel_name='product.attribute', string='Attribute')
   
    value = fields.Many2one( comodel_name='product.attribute.value', string='Value',
                             domain="[('attribute_id', '=', attribute)]")
    
 
    @api.onchange('attribute')
    def onchange_attribute(self):
        self.value = self.attribute.default_value
    
    @api.multi
    def change_all(self):
        article_to_update = self.env['sale.mrp.article']
        product_obj = self.env['product.product']
        for order_attribute in self:
            if order_attribute.order_id:
                for article in order_attribute.order_id.article_ids:
                    for attr in article.product_attributes:
                        if attr.attribute == self.attribute:
                            attr.value = self.value
                            article_to_update |= article
        
        for article in article_to_update:
            article.product_id = product_obj._product_find(article.product_template,
                                                           article.product_attributes) 
            article.explode_bom()  
            #article.resource_ids.change_product_id_and_write()
                 
            

# mai adaug categoria de cost  unde o sa intre manopera de montare lambriu / gips 
# la cantitatea se calculeaza dupa un filtru iar 

class sale_order_line(models.Model):
    _inherit = 'sale.order.line'
    
    item_categ = fields.Selection(ITEM_CATEG, default='normal', string='Item Category')
    
    
 
 
class sale_mrp_article_attribute(models.Model):
    _name = 'sale.mrp.article.attribute'

    _order = 'sequence'
    sequence = fields.Integer(string='Sequence', related="attribute.sequence", store=True)
    
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
    name = fields.Char(string='Name',related='product_template.name')
    product_uom_qty = fields.Float(string='Product Quantity', required=True, digits=dp.get_precision('Product Unit of Measure'))
    qty_formula =  fields.Char(string='Formula for Quantity')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    
    item_categ = fields.Selection(ITEM_CATEG, default='optional', string='Item Category')
    
    #primary_item = fields.Boolean(string='Primary Item')
    #category_id = fields.Many2one('sale.mrp.article.category', string='Article Category')
    
    price_unit =  fields.Float(string='Unit Price', digits= dp.get_precision('Product Price'),compute='_compute_amount',  )
    resource_ids = fields.One2many('sale.mrp.resource',inverse_name='article_id', string="Resources", copy=True)
    amount      = fields.Float( string='Amount', digits= dp.get_precision('Account'), compute='_compute_amount', store=True)   

    #article_property_ids = fields.Many2many('mrp.property', string='Properties', compute='_compute_properties'  , inverse='_inverse_properties', readonly=False)
  
    #property_ids = fields.Many2many('mrp.property', 'sale_order_article_property_rel', 'article_id', 'property_id', 'Properties')

    note = fields.Text(string='Note')


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
    

    @api.onchange('bom_id')
    def onchange_bom(self):
        if self.bom_id:
            self.product_template = self.bom_id.product_tmpl_id
            self.item_categ = 'normal'
            if self.bom_id.product_id:
                self.product_id = self.bom_id.product_id
        self.explode_bom()



    @api.onchange('qty_formula')
    def change_qty_formula(self):   
        if self.qty_formula and self.qty_formula[0]=='=':         
            try:
                formula = self.qty_formula[1:]
                value = eval(formula)
                if value:
                    self.product_uom_qty = value
            except:
                raise Warning('Eroare evaluare formula')
                 

    @api.multi
    def _get_attributes(self):
        self.ensure_one()
        if self.product_id:
            attributes =   self.product_id._get_product_attributes_values_dict() 
        else:
            attributes =   self.product_template._get_product_attributes_dict() 
   
        
        for attr in attributes:
            if not attr.get('value',False):
                attribute = self.env['product.attribute'].browse(attr['attribute'])
                if attribute.default_value:
                    attr['value'] = attribute.default_value.id
                for order_attr in self.order_id.attributes:
                    if attribute.id == order_attr.attribute.id:
                        attr['value'] = order_attr.value.id
            
        return attributes


    @api.onchange('product_template')
    def onchange_product_template(self):
        self.ensure_one()
        #self.name = self.product_template.name
        if not self.product_template.attribute_line_ids:
            self.product_id = ( self.product_template.product_variant_ids and
                                self.product_template.product_variant_ids[0])
        else:
            self.product_id = False
            self.product_uom = self.product_template.uom_id
        
        self.product_attributes = self._get_attributes()


        
        bom_id = self.env['mrp.bom']._bom_find(product_tmpl_id = self.product_template.id)
        bom = self.env['mrp.bom'].browse(bom_id)
        if bom.type == 'phantom':
            self.bom_id = bom
 
         



    @api.onchange('product_attributes')
    def onchange_product_attributes(self):
        product_obj = self.env['product.product']
        self.product_id = product_obj._product_find(self.product_template,
                                                    self.product_attributes)
        self.explode_bom()
        
        
        """ 
        order_attribute_values = []
        article = self     
        for attribute in article.product_attributes:
            if attribute.value:
                order_attribute = self.env['sale.mrp.order.attribute']  
                for order_attr in self.order_id.attributes:
                    if attribute.attribute == order_attr.attribute:
                        order_attribute = order_attr
                if not order_attribute:
                    print "Atribute vechi", self.order_id.attributes 
                    
                    self.order_id.attributes += self.env['sale.mrp.order.attribute'].new({'order_id':self.order_id.id,
                                                                                       'attribute':attribute.attribute.id, 
                                                                                       'value':attribute.value.id})              
                    print  "Atribute noi", self.order_id.attributes
                    for a in self.order_id.attributes:
                        print "Atribute", a.attribute.name, a.value.name, a.order_id.id
        """
        

    @api.onchange('product_id' )
    def onchange_product_id(self):

        if not self.product_id:
            return
         
        #self.name  = self.product_id.with_context(context=self.order_id.partner_id).name_get()[0][1]
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
        
        #attributes = (self.product_id._get_product_attributes_values_dict())
        self.product_attributes = self._get_attributes()

 



 
    @api.onchange('product_uom_qty','item_categ')
    def onchange_product_uom_qty(self):
        self.explode_bom() 
       


    @api.model
    def explode_bom(self):
       
        article = self
        items = []
        if self.bom_id:

            factor = self.env['uom.uom']._compute_qty(self.product_uom.id, self.product_uom_qty, self.bom_id.product_uom.id)

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
                    price_unit = self.env['uom.uom']._compute_price(product.uom_id.id, price_unit, item['product_uom'] )
                else:
                    price_unit = 0
                
                from_currency = self.env.user.company_id.currency_id.with_context(date=self.order_id.date_order)
                purchase_price  = from_currency.compute( product.standard_price or product.product_tmpl_id.standard_price,  self.order_id.pricelist_id.currency_id )
                
                        
                value = {           'product_template':item['product_template'],
                                    'product_id': item['product_id'],
                                    'product_uom_qty': item['product_qty'],
                                    'product_uom': item['product_uom'],
                                    'price_unit': price_unit,
                                    'amount': price_unit * item['product_qty'],
                                    'state':'draft',
                                    'item_categ':item['item_categ'],
                                    'article_id':article.id,
                                    'purchase_price':purchase_price,
                                    }
        
                value['name'] = product.with_context(context=self.order_id.partner_id).name_get()[0][1]
 
                    
                resources += [(0,0,value)]
 
        
         
        resource_ids =  self._convert_to_cache({'resource_ids': resources }, validate=False)
         
        self.update(resource_ids) 
        #for resource in self.resource_ids:
        #    resource.onchange_product_id()
            
        #self.resource_ids = (resources)
        return resource_ids
        #article.order_id.resource_ids.invalidate_cache()            


    @api.multi
    def open_bom(self):
        self.ensure_one()
        if self.bom_id:
            #print "Deschid sublista de materiale"
            return {
                'res_id': self.bom_id.id,
                'domain': "[('id','=', "+str(self.bom_id.id)+")]",
                'name': _('BOM'),
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'mrp.bom',
                'view_id': False,
                'target': 'current',
                'nodestroy': True,   
               'type': 'ir.actions.act_window'             
            }

      
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
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    price_unit  = fields.Float(string='Unit Price', digits = dp.get_precision('Product Price') )
    amount      = fields.Float( string='Amount', digits = dp.get_precision('Account'), compute='_compute_amount', store=True)   
    categ_id    = fields.Many2one('product.category', related='product_id.categ_id', store=True) # este nevoie ? mai bine se aduce informatia direct in raport ?

    purchase_price = fields.Float(string='Purchase Price')
    
    bom_id      =  fields.Many2one('mrp.bom', string='BOM', compute='_compute_get_bom') 

    resource_item_ids = fields.One2many('sale.mrp.resource.item',inverse_name='resource_id', string="Products", copy=True)
    
    # o fi mai bine sa fac un raport in care sa auc camurile
    margin = fields.Float(string='Margin', compute='_compute_margin', store=True)
    purchase_amount = fields.Float(string='Purchase Amount', compute='_compute_margin', store=True)
    currency_id = fields.Many2one('res.currency',  related="order_id.pricelist_id.currency_id", store=True)


    @api.one
    @api.constrains('purchase_price', 'price_unit')
    def _check_price(self):
        if (self.price_unit < self.purchase_price):
            raise ValidationError(_("Sale price for %s must be higher than the purchase price") % self.product_id.name)
 

    @api.one
    @api.depends('price_unit','purchase_price','product_uom_qty')
    def _compute_margin(self):
        self.margin = self.product_uom_qty*self.price_unit - self.product_uom_qty*self.purchase_price
        self.purchase_amount = self.product_uom_qty*self.purchase_price

    @api.one
    @api.depends('product_id')
    def _compute_get_bom(self):
        self.bom_id = self.env['mrp.bom']._bom_find(product_id  = self.product_id.id)


    @api.multi
    @api.depends('price_unit','product_uom_qty')
    def _compute_amount(self):
        for resource in self:
            resource.amount = resource.product_uom_qty * resource.price_unit

    @api.onchange('purchase_price')
    def onchange_purchase_price(self):
        if self.purchase_price and self.product_id and self.order_id and self.order_id.pricelist_id:
            order_id = self.order_id
            
            from_currency =  order_id.pricelist_id.currency_id.with_context( date=order_id.date_order)
            purchase_price  = from_currency.compute( self.purchase_price, self.env.user.company_id.currency_id )
            try:
                self.product_id.write({'standard_price': purchase_price})
            except:
                pass
            
            price =  order_id.pricelist_id.price_get( self.product_id.id, self.product_uom_qty or 1.0,  order_id.partner_id.id)[ order_id.pricelist_id.id]    
            price = self.env['uom.uom']._compute_price(self.product_id.uom_id.id, price, self.product_uom.id )  
            self.price_unit = price
 

    @api.onchange('product_id','product_uom_qty')
    def onchange_product_id(self):
        if self.product_id and self.article_id.order_id and self.article_id.order_id.pricelist_id:
           
            self.product_uom = self.product_id.uom_id
            order_id = self.article_id.order_id
            
            """ 
            # e bine dar dureaza foarte mult sa faca explozia si calculul la fiecare produs in pare 
            bom_id = self.env['mrp.bom']._bom_find( product_id   = self.product_id.id )
            if bom_id:
                bom = self.env['mrp.bom'].browse(bom_id)
                price = bom.with_context(production=self.article_id).get_price(order_id.partner_id,order_id.pricelist_id)
            else:
                price =  order_id.pricelist_id.price_get( self.product_id.id, self.product_uom_qty or 1.0,  order_id.partner_id.id)[ order_id.pricelist_id.id]
            """ 
            # am pus in context atricolul pentru ca se se reia de acolo atributele can de calculeaza pretul
            # am pus dar fara efect ca se pierde pe drum contextul
            # pretul se va caclula manual din BOM prin apasarea unui buton care va face calculul pentru ficare varianta de produs
            price =  order_id.pricelist_id.with_context(production=self.article_id).price_get( self.product_id.id, self.product_uom_qty or 1.0,  order_id.partner_id.id)[ order_id.pricelist_id.id]    
            
            price = self.env['uom.uom']._compute_price(self.product_id.uom_id.id, price, self.product_uom.id ) # nu cred ca e cazul ca sa mai schimb si unitatea de masura 
            self.price_unit = price
            self.name = self.product_id.name
            
            
            from_currency = self.env.user.company_id.currency_id.with_context(date=order_id.date_order)
            
            #print "Pret ", self.product_id.name , " = ", self.product_id.standard_price
            
            self.purchase_price  = from_currency.compute( self.product_id.standard_price or self.product_id.product_tmpl_id.standard_price,  order_id.pricelist_id.currency_id )
            
             
            #result['name'] = self.pool.get('product.product').name_get(cr, uid, [product_obj.id], context=context_partner)[0][1]
            #if self.product_id.description_sale:
            #    self.name += '\n'+self.product_id.description_sale 

    """
    @api.multi
    def change_product_id_and_write (self):
        for resource in self:
             resource.onchange_product_id()
             resource.write({'purchase_price':resource.purchase_price})
    """    


    @api.model
    def explode_product(self, product_id, product_uom_qty,  product_uom_id):
        
        bom_id = self.env['mrp.bom']._bom_find(product_id  =  product_id)
        
        bom = self.env['mrp.bom'].browse(bom_id)
        items = []
        if not bom:
            items =  [{    'product_id':  product_id,  
                            'product_qty': product_uom_qty,
                            'product_uom': product_uom_id,    
                           }] 
        else:
            uom = self.env['uom.uom'].browse(product_uom_id)
            product = self.env['product.product'].browse(product_id)
            
            factor = self.env['uom.uom']._compute_qty(product_uom_id, product_uom_qty, bom.product_uom.id)
            factor =  factor / bom.product_qty
            bom_items, work = bom.with_context(production=self.article_id)._bom_explode(product=product_id, factor = factor)
            for item in bom_items:
                items += self.explode_product(item['product_id'],item['product_qty'],item['product_uom'])
        return items

    @api.model
    def explode_bom(self):

        items = self.explode_product(self.product_id.id,  self.product_uom_qty, self.product_uom.id)
     
        resources = []
        for item in items:         
            value = {   'product_id': item['product_id'],
                        'product_uom_qty': item['product_qty'],
                        'product_uom': item['product_uom'],                            
                        }
            resources += [(0,0,value)]

        resource_item_ids =  self._convert_to_cache({'resource_item_ids': resources }, validate=False)
         
        self.update(resource_item_ids) 
 
        return resource_item_ids



    @api.multi
    def open_bom(self):
        self.ensure_one()
        if self.bom_id:
            #print "Deschid sublista de materiale"
            return {
                'res_id': self.bom_id.id,
                'domain': "[('id','=', "+str(self.bom_id.id)+")]",
                'name': _('BOM'),
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'mrp.bom',
                'view_id': False,
                'target': 'current',
                'nodestroy': True,   
               'type': 'ir.actions.act_window'             
            }                

class sale_mrp_resource_item(models.Model):
    _name = 'sale.mrp.resource.item'
    _description = "Sale Resource Item"       

    order_id  = fields.Many2one('sale.order', related='article_id.order_id', store=True, string='Order', copy=False)
    article_id  = fields.Many2one('sale.mrp.article', related='resource_id.article_id', store=True, string='Article', copy=False, ondelete='cascade')
    resource_id  = fields.Many2one('sale.mrp.resource', string='Resource', copy=False, ondelete='cascade')
    product_id  = fields.Many2one('product.product', string='Product')
    product_uom_qty = fields.Float(string='Product Quantity', required=True, digits =dp.get_precision('Product Unit of Measure'))
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
 
 
    