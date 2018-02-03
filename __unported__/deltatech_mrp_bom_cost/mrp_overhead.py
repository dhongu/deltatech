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
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta



class mrp_production_cost(models.Model):
    _name = 'mrp.production.cost'
    _description = "Production order cost"

    production_id = fields.Many2one('mrp.production', string='Production Order', select=True)
    cost_categ_id = fields.Many2one('mrp.cost.category', string="Cost Category")
    amount = fields.Float(digits= dp.get_precision('Account'), string='Amount')


class mrp_bom_cost(models.Model):
    _name = 'mrp.bom.cost'
    _description = "Production bom cost"

    bom_id = fields.Many2one('mrp.bom', string='BoM', select=True, ondelete='cascade',  required=True)
    cost_categ_id = fields.Many2one('mrp.cost.category', string="Cost Category",  required=True)
    amount = fields.Float(digits= dp.get_precision('Account'), string='Amount', compute='_compute_amount')



    @api.multi
    def get_cost(self, cost_categ):
        cost = self
        amount = 0
        if cost_categ.type == 'normal':
            domain = [('bom_id','=',cost.bom_id)]
            domain.extend(cost_categ.domain)
            bom_lines = self.env['mrp.bom.line'].search(domain)
            for line in bom_lines:
                amount +=  line.calculate_price * line.product_qty 
            amount = amount  * cost_categ.percent  
        else:
            for child_cost_categ in  cost_categ.child_id:
                amount += self.get_cost(child_cost_categ)
        return amount
                     
            


    @api.multi
    def _compute_amount(self):    
        for cost in self:
            cost.amount =  self.get_cost(self.cost_categ_id)
            
                 
            
            


class mrp_cost_category(models.Model):
    _name = 'mrp.cost.category'
    _description = "Cost Category"
  
    # valoare materiale determinate * procent + suma fixa  
    # la costurile de tip view se face insmarea categoriilor inferioare
    
    name = fields.Char(string='Name') #materiale , #manopera,  #utilaje, # transport, #chirie,  #altele
    #base = fields.Selection([('bom_qty','BOM Quantity'),('bom_val','BOM Value')])
    domain = fields.Char(string="Domain", default='[()]')                    #se selecteaza din bom doar liniile utilizand domeniu
    percent = fields.Float(string='Percent', help="For Cost Value percent enter % ratio between 0-1.", default=1.0)   

    type = fields.Selection([('view','View'), ('normal','Normal')], 'Category Type', 
                            help="A category of the view type is a virtual category that can be used as the parent of another category to create a hierarchical structure."),

    parent_id = fields.Many2one('mrp.cost.category',string='Parent Category', select=True, ondelete='cascade')
    
    child_id = fields.One2many('mrp.cost.category', 'parent_id', string='Child Categories')
    parent_left = fields.integer(string='Left Parent', select=1)
    parent_right = fields.integer(string='Right Parent', select=1)
    
    
    
    
    
    
    
    