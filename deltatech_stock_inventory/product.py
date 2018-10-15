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

from datetime import date, datetime
from dateutil import relativedelta

import time
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare, float_is_zero
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from openerp import SUPERUSER_ID, api

import openerp.addons.decimal_precision as dp



class product_template(models.Model):
    _inherit = 'product.template'

    last_inventory_date = fields.Date( string='Last Inventory Date',readonly=True, compute='_compute_last_inventory', store=True)
    last_inventory_id = fields.Many2one('stock.inventory',string='Last Inventory',
                                        readonly=True, compute='_compute_last_inventory', store=True)

    @api.multi
    def get_last_inventory_date(self):
        products = self.env['product.product']
        for template in self:
            products |=   template.product_variant_ids
        products.get_last_inventory_date()


    @api.multi
    def _compute_last_inventory(self):
        for template in self:
            last_inventory_date = False
            last_inventory_id = False
            for product in template.product_variant_ids:
                if last_inventory_date < product.last_inventory_date:
                    last_inventory_date = product.last_inventory_date
                    last_inventory_id = product.last_inventory_id
            template.last_inventory_date = last_inventory_date
            template.last_inventory_id = last_inventory_id


class product_product(models.Model):
    _inherit = 'product.product'

    last_inventory_date = fields.Date(string='Last Inventory Date', readonly=True)
    last_inventory_id = fields.Many2one('stock.inventory',string='Last Inventory', readonly=True)


    @api.multi
    def get_last_inventory_date(self):
        for product in self:
            line = self.env['stock.inventory.line'].search([('product_id','=',product.id),('is_ok','=',True)],
                                                           limit=1, order='id desc')
            if line:
                line.set_last_last_inventory()

