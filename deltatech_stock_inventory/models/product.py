# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from datetime import date, datetime
from dateutil import relativedelta

import time
from odoo.exceptions import except_orm, Warning, RedirectWarning
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
