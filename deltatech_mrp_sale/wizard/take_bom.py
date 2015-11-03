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


class take_bom(models.TransientModel):
    _name = 'sale.mrp.take.bom'
    _description = "Take BOM in Sale Order"
    

    bom_id      =  fields.Many2one('mrp.bom', string='Kit')
    
    
    @api.multi
    def take(self):
        active_id = self.env.context.get('active_id', False)
        sale_order =  self.env['sale.order'].browse(active_id)
        order_line = []
        for item in self.bom_id.bom_line_ids:
            self.env['sale.mrp.article'].create({'product_id':item.product_id.id,
                                                 'product_uom_qty':item.product_qty,
                                                 'product_uom':item.product_uom.id,
                                                 'item_categ':item.item_categ})
        return True
        