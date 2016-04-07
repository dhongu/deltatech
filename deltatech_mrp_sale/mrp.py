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
from openerp.addons.product import _common
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging
import time
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from operator import attrgetter
from itertools import groupby

_logger = logging.getLogger(__name__)


ITEM_CATEG = [('primary','Primary'),
              ('normal','Normal'),
              ('optional','Optional'),
              ('service','Service'),
              ('labor', 'Labor'),
              ('opt_serv','Optional Service')]



class mrp_bom(models.Model):
    _inherit = 'mrp.bom'

    article_list = fields.Boolean(string='Article List')

    @api.model
    def _factor(self, factor, product_efficiency, product_rounding):
        factor = factor / (product_efficiency or 1.0)
        factor = _common.ceiling(factor, product_rounding)
        return factor


    @api.model
    def _prepare_consume_line(self, bom_line, quantity, factor=1):
        res = super(mrp_bom, self)._prepare_consume_line(bom_line, quantity, factor)
        res['item_categ'] = bom_line.item_categ
        return res


    def _check_attribute_in_list(self, check_attribs, component_attribs):
        """ Check if component is suitable for given attributes
        @param check_attribs: Attribute id list
        @param component_attribs: Component defined attributes to check
        @return: Component validity
        """
        getattr = attrgetter('attribute_id')
        for key, group in groupby(component_attribs, getattr):
            if set(check_attribs).intersection([x.id for x in group]):
                return True
        return False    


    # metoda a fost redefinita pentru a selecta o linie daca exista cel putin un atribut
    def _skip_bom_line(self, line, product):
        today = fields.Date.context_today(self)
        if (line.date_start and
                line.date_start > today or
                line.date_stop and (line.date_stop < today)):
            return True
        # all bom_line_id variant values must be in the product
        if line.attribute_value_ids:
            production_attr_values = []
            if not product and self.env.context.get('production'):
                production = self.env.context['production']
                for attr_value in production.product_attributes:
                    production_attr_values.append(attr_value.value.id)
                if not self._check_attribute_in_list(
                        production_attr_values,
                        line.attribute_value_ids):
                    return True
            elif not product or not self._check_product_suitable(
                    product.attribute_value_ids.ids,
                    line.attribute_value_ids):
                return True
        if not line.product_id:
            if not product and self.env.context.get('production'):
                production = self.env.context['production']
                product_attributes = (
                    line.product_template._get_product_attributes_inherit_dict(
                        production.product_attributes))
                comp_product = self.env['product.product']._product_find(
                    line.product_template, product_attributes)
                if not comp_product:
                    return True
        return False


    """
    @api.multi      
    def _bom_explode_variants_categ(
            self,  product, factor, properties=None, level=0,
            routing_id=False, previous_products=None, master_bom=None, product_attributes=None):

        self.ensure_one()
        bom = self
        routing_id = bom.routing_id.id or routing_id
        uom_obj = self.env["product.uom"]
         
        master_bom = master_bom or bom

        def _factor(factor, product_efficiency, product_rounding):
            factor = factor / (product_efficiency or 1.0)
            factor = _common.ceiling(factor, product_rounding)
            #if factor < product_rounding:
            #    factor = product_rounding
            return factor

        factor = _factor(factor, bom.product_efficiency, bom.product_rounding)

        result = []
        production_attr_values = []
        for attr_value in product_attributes:
            if attr_value.value:
                production_attr_values.append(attr_value.value.id)  

        for bom_line_id in bom.bom_line_ids:
                        
            if bom_line_id.date_start and  (bom_line_id.date_start > fields.Date.context_today(self)) or \
               bom_line_id.date_stop  and  (bom_line_id.date_stop < fields.Date.context_today(self)):
                continue
            # all bom_line_id variant values must be in the product
            if bom_line_id.attribute_value_ids:
                if not product and product_attributes:

                    
                    if not self._check_attribute_in_list(    production_attr_values,
                                                            bom_line_id.attribute_value_ids):

                        continue
                elif not product or not self._check_product_suitable(   product.attribute_value_ids.ids,
                                                                        bom_line_id.attribute_value_ids):

                    continue
  
            if previous_products and (bom_line_id.product_id.product_tmpl_id.id
                                      in previous_products):
                raise exceptions.Warning(
                    _('Invalid Action! BoM "%s" contains a BoM line with a'
                      ' product recursion: "%s".') %
                    (master_bom.name, bom_line_id.product_id.name_get()[0][1]))

            quantity = _factor(bom_line_id.product_qty * factor,
                               bom_line_id.product_efficiency,
                               bom_line_id.product_rounding)


            if not bom_line_id.product_id:
                if not bom_line_id.type != "phantom":
                    bom_id = self._bom_find( product_tmpl_id=bom_line_id.product_template.id,
                                             properties=properties)
                else:
                    bom_id = False
            else:
                bom_id = self._bom_find(product_id=bom_line_id.product_id.id,
                                        properties=properties)

            if (bom_line_id.type != "phantom" and
                    (not bom_id or self.browse(bom_id).type != "phantom")):

                
                
                if not bom_line_id.product_id  and product_attributes:
                    item_product_attributes = ( bom_line_id.product_template._get_product_attributes_inherit_dict(product_attributes))
                    comp_product = self.env['product.product']._product_find(  bom_line_id.product_template, item_product_attributes)
                else:
                    comp_product = bom_line_id.product_id
                    item_product_attributes = (  bom_line_id.product_id. _get_product_attributes_values_dict())
                    
                result.append({
                    'name': (bom_line_id.product_id.name or
                             bom_line_id.product_template.name),
                    'product_id': comp_product and comp_product.id,
                    'product_template': (
                        bom_line_id.product_template.id or
                        bom_line_id.product_id.product_tmpl_id.id),
                    'product_qty': quantity,
                    'product_uom': bom_line_id.product_uom.id,
                    'product_uos_qty': (
                        bom_line_id.product_uos and
                        _factor((bom_line_id.product_uos_qty * factor),
                                bom_line_id.product_efficiency,
                                bom_line_id.product_rounding) or False),
                    'product_uos': (bom_line_id.product_uos and
                                    bom_line_id.product_uos.id or False),
                    'product_attributes': map(lambda x: (0, 0, x),
                                              item_product_attributes),
                    #'level':level,
                    'item_categ':bom_line_id.item_categ,
                    #'row': bom_id is False
                })
            
            elif bom_id:
                all_prod = [bom.product_tmpl_id.id] + (previous_products or [])
                bom2 = self.browse(bom_id)
                # We need to convert to units/UoM of chosen BoM
                factor2 = uom_obj._compute_qty(
                    bom_line_id.product_uom.id, quantity, bom2.product_uom.id)
                quantity2 = factor2 / bom2.product_qty
                res = bom2._bom_explode_variants_categ(  bom_line_id.product_id, quantity2,
                    properties=properties, level=level + 1,
                    previous_products=all_prod, master_bom=master_bom, product_attributes = product_attributes)
                result = result + res
            else:
                if not bom_line_id.product_id:
                    name = bom_line_id.product_template.name_get()[0][1]
                else:
                    name = bom_line_id.product_id.name_get()[0][1]
                raise exceptions.Warning(
                    _('Invalid Action! BoM "%s" contains a phantom BoM line'
                      ' but the product "%s" does not have any BoM defined.') %
                    (master_bom.name, name))

        return result
    """

    def _bom_find(self, cr, uid, product_tmpl_id=None, product_id=None, properties=None, context=None):
        """ Finds BoM for particular product and product uom.
        @param product_tmpl_id: Selected product.
        @param product_uom: Unit of measure of a product.
        @param properties: List of related properties.
        @return: False or BoM id.
        """
        if not context:
            context = {}
        if properties is None:
            properties = []
        if product_id:
            if not product_tmpl_id:
                product_tmpl_id = self.pool['product.product'].browse(cr, uid, product_id, context=context).product_tmpl_id.id
            domain = [
                '|',
                    ('product_id', '=', product_id),
                    '&',
                        ('product_id', '=', False),
                        ('product_tmpl_id', '=', product_tmpl_id)
            ]
        elif product_tmpl_id:
            #domain = [('product_id', '=', False), ('product_tmpl_id', '=', product_tmpl_id)]
            domain = [ ('product_tmpl_id', '=', product_tmpl_id)]
        else:
            # neither product nor template, makes no sense to search
            return False
        if context.get('company_id'):
            domain = domain + [('company_id', '=', context['company_id'])]
        domain = domain + [ '|', ('date_start', '=', False), ('date_start', '<=', time.strftime(DEFAULT_SERVER_DATE_FORMAT)),
                            '|', ('date_stop', '=', False), ('date_stop', '>=', time.strftime(DEFAULT_SERVER_DATE_FORMAT))]
        # order to prioritize bom with product_id over the one without
        ids = self.search(cr, uid, domain, order='sequence, product_id', context=context)
        # Search a BoM which has all properties specified, or if you can not find one, you could
        # pass a BoM without any properties with the smallest sequence
        bom_empty_prop = False
        for bom in self.pool.get('mrp.bom').browse(cr, uid, ids, context=context):
            if not set(map(int, bom.property_ids or [])) - set(properties or []):
                if not properties or bom.property_ids:
                    return bom.id
                elif not bom_empty_prop:
                    bom_empty_prop = bom.id
        return bom_empty_prop




class mrp_bom_line(models.Model):
    _inherit = 'mrp.bom.line'   
    
    item_categ = fields.Selection(ITEM_CATEG, default='normal', string='Item Category')

    child_bom_id = fields.Many2one('mrp.bom',string="Child BOM", compute="_compute_child_bom")


    @api.multi
    @api.depends('product_template','product_id')
    def _compute_child_bom(self):
        for bom_line in self:
           bom_id = self.env['mrp.bom']._bom_find(product_tmpl_id=bom_line.product_template.id,
                                                   product_id=bom_line.product_id.id, 
                                                   properties=bom_line.property_ids )
           bom_line.child_bom_id = self.env['mrp.bom'].browse( bom_id )
             


    @api.multi
    @api.depends('product_template','product_id')
    def _calculate_standard_price(self): 
        for bom_line in self:
            if bom_line.product_id:
                bom_line.standard_price = bom_line.product_id.standard_price  
            else:
                bom_line.standard_price = bom_line.product_template.standard_price 
            


    @api.multi
    @api.depends('product_template','product_id','child_bom_id')
    def _calculate_price(self):
        for bom_line in self:            
            if bom_line.child_bom_id:
                price = bom_line.child_bom_id.calculate_price
            else:
                if bom_line.product_id:
                    price = bom_line.product_id.standard_price
                else:
                   price = bom_line.product_template.standard_price  
            
            bom_line.calculate_price = price

    
        

    def _get_child_bom_lines(self, cr, uid, ids, field_name, arg, context=None):
        """If the BOM line refers to a BOM, return the ids of the child BOM lines"""
        bom_obj = self.pool['mrp.bom']
        res = {}
        for bom_line in self.browse(cr, uid, ids, context=context):
            bom_id = bom_obj._bom_find(cr, uid,
                product_tmpl_id=bom_line.product_template.id,
                product_id=bom_line.product_id.id, context=context)
            if bom_id:
                child_bom = bom_obj.browse(cr, uid, bom_id, context=context)
                res[bom_line.id] = [x.id for x in child_bom.bom_line_ids]
            else:
                res[bom_line.id] = False
        return res   
    
    _sql_constraints = [
        ('bom_qty_zero', 'CHECK (1=1)', 'Error'),
    ]    

    @api.multi
    def open_bom(self):
        self.ensure_one()
        if self.child_bom_id:
            #print "Deschid sublista de materiale"
            return {
                'res_id': self.child_bom_id.id,
                'domain': "[('id','=', "+str(self.child_bom_id.id)+")]",
                'name': _('BOM'),
                'view_type': 'form',
                'view_mode': 'form,tree',
                'res_model': 'mrp.bom',
                'view_id': False,
                'target': 'current',
                'nodestroy': True,   
               'type': 'ir.actions.act_window'             
            }
  
    @api.multi
    def check_line(self):
        for line in self:
            if not line.product_id:
                if line.product_template.product_variant_count == 1:
                    for product in line.product_template.product_variant_ids:
                        line.write({'product_id':product.id})
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
