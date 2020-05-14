# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
from datetime import datetime


class PropertyBuilding(models.Model):
    _inherit = 'property.building'

    tenant_id = fields.Many2one('res.partner', string="Tenant")
    agreement_id = fields.Many2one('service.agreement', string='Agreement')