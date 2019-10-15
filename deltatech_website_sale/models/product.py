# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import SUPERUSER_ID
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta


class product_template(models.Model):
    _inherit = 'product.template'

    # #008a00!important  - in stoc
    # #c45500!important  - la comanda  Usually dispatched within 4 to 5 days.

    # exista  inventory_availability cu care trebuie sa existe o relatie
    is_qty_available = fields.Selection(
        [('stock', 'In Stock'), ('provider', 'In provider stock'), ('order', 'At Order')], compute="_compute_available")
    at_order = fields.Boolean(string="Available at order")

    inventory_availability = fields.Selection(default='threshold')
    available_threshold = fields.Float(default=1.0)

    @api.multi
    @api.depends('qty_available','at_order')
    def _compute_available(self):
        res = {}
        for product in self:
            if product.sudo().qty_available > 0:
                product.is_qty_available = 'stock'
            else:
                if product.at_order:
                    product.is_qty_available = 'order'
                else:
                    product.is_qty_available = 'provider'
        return res

