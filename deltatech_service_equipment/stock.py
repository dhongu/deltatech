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


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


class stock_picking(models.Model):
    _inherit = "stock.picking"

    
    equipment_history_id = fields.Many2one('service.equipment.history', string='Equipment history')    
    equipment_id = fields.Many2one('service.equipment', string='Equipment', related='equipment_history_id.equipment_id' ,store=True)
    agreement_id = fields.Many2one('service.agreement', string='Service Agreement', related='equipment_history_id.agreement_id',store=True)
    



#todo:  raport cu piesele consumate pe fiecare echipament / contract - raportat cu numarul de pagini tiparite 
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: