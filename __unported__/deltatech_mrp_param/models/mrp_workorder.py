# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    parameter_value_ids = fields.One2many('mrp.parameter.value', 'workorder_id', string='Parameter')


    @api.multi
    def button_copy_param(self):
        values = []
        for workorder in self:
            for parameter_value in workorder.operation_id.parameter_value_ids:
                values += [{
                    'parameter_id': parameter_value.parameter_id.id,
                    'value': parameter_value.parameter_id.value,
                    'workorder_id': workorder.id
                }]

        if values:
            self.env['mrp.parameter.value'].create(values)
