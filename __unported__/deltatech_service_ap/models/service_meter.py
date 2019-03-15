# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
import math
from datetime import datetime

import logging

_logger = logging.getLogger(__name__)


class service_meter(models.Model):
    _inherit = 'service.meter'

    equipment_id = fields.Many2one('service.equipment', string='Apartment', required=True, ondelete='cascade',
                                   index=True)


class service_meter_reading(models.Model):
    _inherit = 'service.meter.reading'

    equipment_id = fields.Many2one('service.equipment', string='Apartment', required=True, ondelete='restrict')
