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



class service_efficiency_report(models.Model):
    _name = "service.efficiency.report"
    _inherit = "stock.picking.report"   


    equipment_id = fields.Many2one('service.equipment', string='Equipment', index=True) 
    agreement_id = fields.Many2one('service.agreement', string='Contract Services')      
    usage =  fields.Float( string='Usage',   digits =dp.get_precision('Product UoM'), readonly=True, compute="_compute_usage"  ,store=True  )
    uom_usage = fields.Many2one('product.uom', string='Unit of Measure Usage', help="Unit of Measure for Usage", index=True) 
    shelf_life = fields.Float(string='Shelf Life',  digits =dp.get_precision('Product UoM')  )


    def _select(self):
        select_str = super(service_efficiency_report,self)._select() + """,
                  hist.equipment_id, 
                  hist.agreement_id, 
                  0 as usage, 
                  sum(sq.qty)*avg(pt.shelf_life) as shelf_life, 
                  pt.uom_shelf_life as uom_usage
                """
        return select_str     

    def _from(self):
        from_str = super(service_efficiency_report,self)._from() + """
                       INNER JOIN service_equipment_history as hist ON sp.equipment_history_id = hist.id 
                       INNER JOIN service_equipment as equi ON  hist.equipment_id = equi.id 
                    """
        return from_str
    
    def _group_by(self):       
        group_by_str =  super(service_efficiency_report,self)._group_by() + ', hist.equipment_id, hist.agreement_id, pt.uom_shelf_life'
        return group_by_str

     
    @api.one
    def _compute_usage(self):
        self.usage = 0.0
        # se cauta consumul anterior 
        

    def read_group(self, cr, uid, domain, fields, groupby, offset=0, limit=None, context=None, orderby=False, lazy=True):  
        res = super(service_efficiency_report, self).read_group(cr, uid, domain, fields, groupby, offset=offset, limit=limit, context=context, orderby=orderby, lazy=lazy)
        
        if 'usage' in fields:
            usage = 0
            group_lines = {}
            for line in res:
                begin_date = '2000-01-01'
                end_date   = '2999-12-31'
                product_id = False
                uom_usage = False
                equipment_id = False
                domain = line.get('__domain', [])
                for cond in domain:
                    if cond[0] == 'date':
                        if cond[1] == '>=' or cond[1] == '>':
                            begin_date = cond[2]
                        if cond[1] == '<' or cond[1] == '<=':
                            end_date = cond[2]
                    if cond[0] == 'equipment_id':
                        equipment_id = cond[2]
                    if cond[0] == 'product_id':
                        product_id = cond[2]
                    if cond[0] == 'uom_usage':
                        uom_usage = cond[2]
                
                usage = self.get_usage(cr,uid, begin_date,end_date, equipment_id, uom_usage, product_id)
                    
                line['usage'] = usage
                
                
        return res
    

    @api.model
    def get_usage(self,begin_date,end_date, equipment_id, uom_usage, product_id  ):
        
        usage = 0
        if not uom_usage and  product_id:
                product = self.env['product.product'].browse(product_id)
                if product:
                    uom_usage = product.uom_shelf_life.id  

        if uom_usage and equipment_id:   
            uom = self.env['product.uom'].browse(uom_usage)
            meters = self.env['service.meter'].search([('equipment_id','=',equipment_id),('uom_id.category_id','=',uom.category_id.id)]) 
            
            if meters:
                meter_find = meters[0]
            else:
                meter_find = False
                
            for meter in meters:
                if meter.uom_id == uom:
                    meter_find = meter
                    
            if meter_find:
                usage = meter_find.get_counter_value(begin_date,end_date)
                from_uom = meter_find.uom_id
                to_uom = uom
                usage = usage/from_uom.factor
                usage = usage * to_uom.factor

        
        if not uom_usage or not equipment_id:
            domain =  [('date', '>=', begin_date ), ('date', '<', end_date)]
            fields=['equipment_id','uom_usage','usage']
            groupby=['equipment_id','uom_usage']
            if  product_id:   
                domain += [('product_id','=',product_id)]  
                fields += ['product_id']
                groupby += ['product_id']
            if equipment_id:
                domain += [('equipment_id','=',equipment_id)]  
            if uom_usage:
                domain += [('uom_usage','=',uom_usage)]                 
            res = self.read_group( domain=domain, fields=fields, groupby=groupby,lazy=False)
            for line in res:
                usage += line['usage']
       
        return usage
            
        
               
        
        
    