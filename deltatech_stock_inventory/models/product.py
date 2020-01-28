# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from datetime import date, datetime
from dateutil import relativedelta

import time
from odoo.exceptions import UserError, RedirectWarning
from odoo.tools import float_compare, float_is_zero
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo import SUPERUSER_ID, api

import odoo.addons.decimal_precision as dp


class product_template(models.Model):
    _inherit = 'product.template'

    loc_rack = fields.Char('Rack', size=16)
    loc_row = fields.Char('Row', size=16)
    loc_case = fields.Char('Case', size=16)

    last_inventory_date = fields.Date(string='Last Inventory Date', readonly=True, compute='_compute_last_inventory',
                                      store=True)
    last_inventory_id = fields.Many2one('stock.inventory', string='Last Inventory',
                                        readonly=True, compute='_compute_last_inventory', store=True)

    @api.multi
    def get_last_inventory_date(self):
        products = self.env['product.product']
        for template in self:
            products |= template.product_variant_ids
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
    last_inventory_id = fields.Many2one('stock.inventory', string='Last Inventory', readonly=True)

    @api.multi
    def get_last_inventory_date(self):
        for product in self:
            line = self.env['stock.inventory.line'].search([('product_id', '=', product.id), ('is_ok', '=', True)],
                                                           limit=1, order='id desc')
            if line:
                line.set_last_last_inventory()
            product.write({'last_inventory_date':fields.Date.today()})
