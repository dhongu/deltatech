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
import logging
from odoo.osv.fields import related

from odoo.addons.product import _common

_logger = logging.getLogger(__name__)


 
class ProductProduct(models.Model):
    _inherit = 'product.product'
    attribute_value_ids = fields.Many2many(readonly=False)

class product_attribute(models.Model):
    _inherit = 'product.attribute'

    _order = 'sequence'
    
    default_value = fields.Many2one('product.attribute.value',  string='Default Value', copy=True)
    sequence = fields.Integer(string='Sequence', help="Determine the display order")


class product_attribute_line(models.Model):
    _inherit = "product.attribute.line"
    _order = 'sequence'
    sequence = fields.Integer(string='Sequence', related="attribute_id.sequence", store=True)
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: