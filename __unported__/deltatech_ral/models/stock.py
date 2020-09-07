# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _


class stock_production_lot(models.Model):
    _inherit = 'stock.production.lot'

    ral_id = fields.Many2one('product.product', 'RAL', index=True, domain=[('default_code', 'like', 'RAL%')])
