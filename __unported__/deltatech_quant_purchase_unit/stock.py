# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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

from odoo import models, fields, api, tools, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.api import Environment

 
class stock_quant(models.Model):
    _inherit = "stock.quant"   
    
    
    qty_po_uom = fields.Float(string="Quantity in Purchase Unit", compute="_compute_qty_po")
    uom_po_id  = fields.Many2one('uom.uom', string='Purchase Unit of Measure', related='product_id.uom_po_id')
    uom_id  = fields.Many2one('uom.uom', string='Unit of Measure', related='product_id.uom_id')

    @api.multi
    def _compute_qty_po(self):
        for quant in self:
            quant.qty_po_uom = self.env['uom.uom']._compute_qty_obj(quant.product_id.uom_id, quant.qty, quant.uom_po_id )









# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
