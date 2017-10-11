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
#
##############################################################################


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
 



class service_consumable(models.Model):
    _name = 'service.consumable'
    _description = "Consumable List"

    name = fields.Char(string='Name')
    categ = fields.Selection([('type','Type'),('product', 'Product')])
    type_id = fields.Many2one('service.equipment.type', string="Type", ondelete='restrict',)  
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict', domain=[('type', '=', 'product')] )    
    item_ids =  fields.One2many('service.consumable.item', 'consumable_id', string='Consumable')


    @api.onchange('categ','type_id','product_id')
    def onchange_categ(self):
        if self.categ == 'type':
            self.name = self.type_id.name
        else:
            self.name = self.product_id.name
    
  
class service_consumable_item(models.Model):
    _name = 'service.consumable.item'
    _description = "Consumable Item"

    name = fields.Char(string='Name', related='product_id.name')
    consumable_id =  fields.Many2one('service.consumable', string='Consumable List', ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Consumable', ondelete='restrict', domain=[('type', '=', 'product')] ) 
    quantity = fields.Float(string='Quantity', compute='_compute_quantity', digits= dp.get_precision('Product Unit of Measure') )
    shelf_life = fields.Float(string='Shelf Life', related='product_id.shelf_life')
    uom_shelf_life = fields.Many2one(string='Shelf Life UoM', related='product_id.uom_shelf_life')
    colors = fields.Char("HTML Colors Index",default="['#a9d70b', '#f9c802', '#ff0000']")
    max_qty = fields.Float(string='Quantity Max', digits= dp.get_precision('Product Unit of Measure'), help="Maximum Quantity allowed" )

    @api.one
    def _compute_quantity(self):
        equipment_id = self.env.context.get('equipment_id',False)
        self.quantity = 0.0
        if equipment_id:
            eff = self.env['service.efficiency.report']         
            domain = [('product_id','=',self.product_id.id),('equipment_id','=',equipment_id)] 
            fields=['equipment_id','product_id','usage','shelf_life']
            groupby =['equipment_id','product_id']
            res = eff.read_group( domain=domain, fields=fields, groupby=groupby,lazy=False)
            for line in res:
                self.quantity += line['shelf_life'] - line['usage']
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: