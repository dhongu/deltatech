# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api


class MrpParameter(models.Model):
    _name = 'mrp.parameter'
    _description = "Mrp Parameter"

    display_name = fields.Char(string='Name', compute='_compute_display_name')
    name = fields.Char()
    code = fields.Char(index=True,  required=True)
    value_ids = fields.One2many('mrp.parameter.value', 'parameter_id', string='Values')
    value = fields.Float('Default Value', required=True, default=0.0)


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        recs = self.search(domain + args, limit=limit)
        return recs.name_get()



    @api.multi
    @api.depends('code')
    def _compute_display_name(self):
        for item in self:
            if item.code and self.env.context.get('display_code', False):
                item.display_name = '%s - %s' % (item.code, item.name)
            else:
                item.display_name = item.name


class MrpParameterValue(models.Model):
    _name = 'mrp.parameter.value'
    _description = "Mrp Parameter Value"


    date =  fields.Datetime('Measurement date', default=fields.Datetime.now)
    value = fields.Float('Value', required=True)
    qty_min = fields.Float('Minim', required=True, default=0.0)
    qty_max = fields.Float('Maxim', required=True, default=99999.0)

    parameter_id = fields.Many2one('mrp.parameter', string='Parameter')
    workcenter_id = fields.Many2one('mrp.workcenter', 'Work Center')
    product_id = fields.Many2one('product.template', string='Product Template')

    workorder_id = fields.Many2one('mrp.workorder', string='Work Order')
    routing_workcenter_id = fields.Many2one('mrp.routing.workcenter', string='Routing Operation')


    @api.onchange('value')
    def onchange_value(self):
        self.date = fields.Datetime.now()


