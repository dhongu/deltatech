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

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import   Warning, RedirectWarning



class product_template(models.Model):
    _inherit = 'product.template'

    dimensions = fields.Char(string='Dimensions' )
    shelf_life = fields.Float(string='Shelf Life',  digits =dp.get_precision('Product UoM') )
    uom_shelf_life = fields.Many2one('product.uom', string='Unit of Measure Shelf Life', help="Unit of Measure for Shelf Life",  group_operator="avg")




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: