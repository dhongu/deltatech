# -*- coding: utf-8 -*-
# ©  2015-2020 Deltatech
# See README.rst file on addons root folder for license details

import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError

import unicodedata




class DeliveryCarrier(models.Model):
    _inherit = 'delivery.carrier'

    acquirer_allowed_ids = fields.Many2many('payment.acquirer', string='Payments Acquirer Allowed')