# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    code = fields.Char(string="Code", index=True, related='operation_id.code', readonly=True)
    partner_id = fields.Many2one('res.partner', string="Operator")  # unul din operatori
    total_cost = fields.Float(string="Total Cost")
