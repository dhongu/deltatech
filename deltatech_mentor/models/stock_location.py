# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

import odoo.addons.decimal_precision as dp


class Location(models.Model):
    _inherit = "stock.location"

    code = fields.Char()
