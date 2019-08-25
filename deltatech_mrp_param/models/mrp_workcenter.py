# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api
from odoo.exceptions import UserError
from odoo.tools.translate import _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    parameter_value_ids = fields.One2many('mrp.parameter.value', 'workcenter_id', string='Parameter')
