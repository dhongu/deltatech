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
import odoo.addons.decimal_precision as dp
 



class product_uom_categ(models.Model):
    _inherit = 'product.uom.categ'
    
    product_template_id = fields.Many2one('product.template', string='Product Template' )



class product_uom(models.Model):
    _inherit = 'uom.uom'
    
    description = fields.Char(string="Additional description")
    
        
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        return self.with_context(show_product=True)._name_search(name, args, operator, limit=limit)

    @api.multi
    def name_get(self):
        res = []
        show_product = self.env.context.get('show_product',False)
        if show_product:
            for unit in self:
                name = unit.name 
                if unit.category_id.product_template_id:
                    name = "%s (%s)" %(name,unit.category_id.product_template_id.name )
                if unit.description:
                    name = "%s [%s]" % (name,unit.description )
                res.append((unit.id, name))  
        else:
            res = super(product_uom,self).name_get()           
                    
        return res  
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: