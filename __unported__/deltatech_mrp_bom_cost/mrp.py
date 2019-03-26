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

from odoo.exceptions import except_orm, Warning, RedirectWarning,ValidationError
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp



class mrp_production(models.Model):
    _inherit = 'mrp.production'

    amount = fields.Float(digits= dp.get_precision('Account'), string='Production Amount', compute='_calculate_amount')
    calculate_price = fields.Float(digits= dp.get_precision('Account'), string='Calculate Price', compute='_calculate_amount')
 

    @api.one
    def _calculate_amount(self ):
        production = self  
        calculate_price = 0.0
        amount = 0.0
        if not production.move_lines2:                
            for move in production.move_lines:
                for quant in move.reserved_quant_ids:
                    if quant.qty > 0:
                        amount +=   quant.cost * quant.qty  # se face calculul dupa quanturile planificate
            calculate_price = amount / production.product_qty
            amount = 0.0          
        else:
            for move in production.move_lines2:
                for quant in move.quant_ids:
                    if quant.qty > 0:
                        amount +=   quant.cost * quant.qty
            product_qty = 0.0
            for move in production.move_created_ids2:
                product_qty += move.product_qty
            if product_qty == 0.0:
                product_qty =   production.product_qty
            calculate_price = amount / product_qty  

        production.calculate_price = calculate_price
        production.amount  = amount




    def action_produce(self, cr, uid, production_id, production_qty, production_mode, wiz=False, context=None):
        production = self.browse(cr, uid, production_id, context=context)
            
        if production.product_id.cost_method == 'fifo' and production.product_id.standard_price != production.calculate_price:
            self.pool.get('product.product').write(cr,uid,[production.product_id.id],{'standard_price':production.calculate_price})
        
        res = super(mrp_production,self).action_produce(cr, uid, production_id, production_qty, production_mode, wiz, context)

        self.assign_picking(cr, uid, [production_id], context)
                    
        return res

 
    @api.multi
    def assign_picking(self):
        """
        Totate produsele consumate se vor reuni intr-un picking list 
        """
        for production in self:
            move_list = self.env['stock.move']
            for move in production.move_lines2:
                if not move.picking_id:
                    move_list += move
            if move_list:
                picking_type = self.env.ref('stock.picking_type_consume',raise_if_not_found=False)
                if not picking_type:
                    picking_type  = self.env.ref('stock.picking_type_internal',raise_if_not_found=False)
                
                if picking_type: 
                    picking = self.env['stock.picking'].create({'picking_type_id':picking_type.id,
                                                                'date':production.date_planned,
                                                                'origin':production.name})                    
                    move_list.write({'picking_id':picking.id})
                    picking.get_account_move_lines()
     
        """
        Totate produsele receptionte  se vor reuni intr-un picking list?? 
        """
        
class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    # metoda este buna dar consumatoare de timp
    """
    @api.model
    def get_price(self, partner, pricelist):  
        amount = 0
        #print "Determinare pret pentru ", self.name, partner, pricelist
        
        uom_obj = self.env['uom.uom']
 
             
        results, results2 = self._bom_explode(  self.product_id, 1 )


        for line in results:
            if line['product_id']:
                line_product = self.env['product.product'].browse(line['product_id'])
                product_qty = self.env['uom.uom']._compute_qty( from_uom_id = line['product_uom'],  
                                                                    qty = line['product_qty'],
                                                                    to_uom_id = line_product.uom_id.id, 
                                                                    round = False)
                
                
                item_bom_id = self.env['mrp.bom']._bom_find(product_id  = line['product_id'] )
                if item_bom_id:
                    item_bom = self.env['mrp.bom'].browse(item_bom_id)
                    price = item_bom.get_price(partner,pricelist)
                else:
                    price =  pricelist.price_get( line['product_id'], line['product_qty'],  partner.id)[pricelist.id]
                
                
                #price =  pricelist.price_get( line['product_id'], line['product_qty'],  partner.id)[pricelist.id]
                amount +=  price * product_qty 
                print " Pret pentru ",  line_product.name, ' este ' , price, " conform listei ", pricelist.name
            else:
                price = 0
             
            
             
        price = amount / self.product_qty + amount/self.product_qty*self.value_overhead
        #print price
        return price
    """

    """
    @api.model
    def _prepare_consume_line(self, bom_line, quantity, factor=1):
        res = super(mrp_bom,self)._prepare_consume_line(bom_line, quantity, factor)
        #res['calculate_price'] = bom_line.calculate_price
        return res 
    """     

    # aici nu se tine cont de variante de configurare

    @api.multi
    @api.depends('value_overhead','bom_line_ids','value_overhead')
    def _calculate_price(self):
        for bom in self:
            amount = 0
            
            if 'production' in self.env.context: 
                items, work = bom._bom_explode(product=None, factor=1)
                 
                for item in items:
                    product_qty = item['product_qty']
                    line_product = self.env['product.product'].browse(item['product_id'])
                    # de facut conversia dintre unitate de masura din bom si cea din produs
                    price = line_product.bom_price
                    
                    product_qty = self.env['uom.uom']._compute_qty( from_uom_id = item['product_uom'],
                                                                        qty = item['product_qty'],
                                                                        to_uom_id = line_product.uom_id.id, 
                                                                        round = False)
                    
                    amount += price * product_qty
                    #print "Line: ", item['name'], price, product_qty
            else:
                for line in bom.bom_line_ids:                  
                    product_qty = self.env['uom.uom']._compute_qty( from_uom_id = line.product_uom.id,
                                                                        qty = line.product_qty,
                                                                        to_uom_id = line.product_id.uom_id.id, 
                                                                        round = False)
                     
                    amount +=  line.calculate_price * product_qty  
            price = amount / bom.product_qty + amount/bom.product_qty*bom.value_overhead
            bom.calculate_price = price
 
    @api.multi
    @api.depends('product_id','product_tmpl_id')
    def _calculate_standard_price(self):
        for bom in self:
            if bom.product_id:
                bom.standard_price = bom.product_id.standard_price or bom.product_tmpl_id.standard_price
            else:
                bom.standard_price = bom.product_tmpl_id.standard_price
                

    #name = fields.Char( store=True, compute='_compute_name')   
    value_overhead = fields.Float(string='Value Overhead', help="For Value Overhead percent enter % ratio between 0-1.", default='0.0')
    calculate_price = fields.Float(compute='_calculate_price',  digits = dp.get_precision('Account'), store=False, string='Calculate Price')
    standard_price = fields.Float(compute='_calculate_standard_price',  digits = dp.get_precision('Product Price'),store=False, string="Cost Price")  
     

    """
    @api.multi
    @api.depends('product_id','product_tmpl_id','position')
    def _compute_name(self):
        for bom in self:
            if bom.product_id:
                bom.name = '[%s] %s' % (bom.position, bom.product_id.name)
            elif bom.product_tmpl_id.name:
                bom.name = '[%s] %s' % (bom.position, bom.product_tmpl_id.name)
    """
    
    @api.one
    @api.constrains('value_overhead')
    def _check_overhead(self):
        if ( self.value_overhead < 0.0 or self.value_overhead > 1.0):
            raise ValidationError("Percentages for Value Overhead must be between 0 and 1, Example: 0.02 for 2%")
 

    """
    pentru ce am facut metoda asta ????
    def _bom_explode(self, cr, uid, bom, product, factor, properties=None, level=0, routing_id=False, previous_products=None, master_bom=None, context=None):
        result, result2 = super(mrp_bom,self)._bom_explode(cr, uid, bom, product, factor, properties, level, routing_id, previous_products, master_bom, context)
        uom_obj = self.pool.get('uom.uom')
        for res in result:
            res['product_qty'] = uom_obj._compute_qty(cr, uid, res['product_uom'], res['product_qty'], res['product_uom'] )
        return result, result2
    """


    @api.multi
    def button_set_standard_price(self):
        for bom in self:
            if bom.product_id:
                bom.product_id.write({'standard_price':bom.calculate_price})
            else:
                bom.product_tmpl_id.write({'standard_price':bom.calculate_price})



                
            



class mrp_bom_line(models.Model):
    _inherit = 'mrp.bom.line'


    calculate_price = fields.Float(compute='_calculate_price',  digits = dp.get_precision('Account'), store=False, string='Calculate Price')
    standard_price = fields.Float(compute='_calculate_standard_price',  digits = dp.get_precision('Product Price'),store=False, string="Cost Price")  
    amount = fields.Float(digits= dp.get_precision('Account'), string='Amount', compute='_calculate_amount')

    @api.multi
    @api.depends('calculate_price','product_qty')
    def _calculate_amount(self):
        for bom_line in self:   
            product_qty = self.env['uom.uom']._compute_qty( from_uom_id = bom_line.product_uom.id,
                                                                    qty = bom_line.product_qty,
                                                                    to_uom_id = bom_line.product_id.uom_id.id, 
                                                                    round = False)
                 
            bom_line.amount =  bom_line.calculate_price * product_qty 
            
                

    @api.multi
    def _calculate_price(self):
        for bom_line in self:
            bom_id = self.env['mrp.bom']._bom_find(product_tmpl_id=bom_line.product_id.product_tmpl_id.id,
                                                   product_id=bom_line.product_id.id, properties=bom_line.property_ids )
            if bom_id:
                child_bom = self.env['mrp.bom'].browse( bom_id )
                price = child_bom.calculate_price
            else:
                price = bom_line.product_id.standard_price   or bom_line.product_id.product_tmpl_id.standard_price
            bom_line.calculate_price = price

    

    @api.multi
    @api.depends('product_id')
    def _calculate_standard_price(self): 
        for bom_line in self:
            bom_line.standard_price = bom_line.product_id.standard_price or bom_line.product_id.product_tmpl_id.standard_price
 
                   
        
        


