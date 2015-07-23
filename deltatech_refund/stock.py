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



from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
import openerp.addons.decimal_precision as dp



class stock_picking(models.TransientModel):
    _inherit = "stock.picking"


    # camp pt a indica din ce picking se face stornarea
    origin_refund_picking_id = fields.Many2one('stock.picking', string='Origin Picking',   copy=False)
    # camp prin care se indica prin ce picking se face rambursarea 
    refund_picking_id = fields.Many2one('stock.picking', string='Refund Picking',    copy=False)  #posibil sa fie necesare mai multe intrari many2many
    
    with_refund = fields.Boolean(string="With refund",help="Picking list with refund or is an refund")
    
    