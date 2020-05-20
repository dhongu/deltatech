# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
import math
from dateutil.relativedelta import relativedelta
from datetime import date, datetime


class service_equipment(models.Model):
    _inherit = 'service.equipment'

    internal_type = fields.Selection(selection_add=[('building', 'Building')])


