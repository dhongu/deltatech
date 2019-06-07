# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

import odoo.addons.decimal_precision as dp


class stock_picking(models.Model):
    _name = 'stock.picking'
    _inherit = 'stock.picking'

    notice = fields.Boolean('Is a notice', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]},
                            default=False)
