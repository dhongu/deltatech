# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import UserError




class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'


    parameter_value_ids = fields.One2many('mrp.parameter.value', 'routing_workcenter_id', string='Parameter')


