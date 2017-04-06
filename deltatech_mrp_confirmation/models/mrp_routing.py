
# -*- coding: utf-8 -*-

from odoo import models, fields, api, _



class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    code = fields.Char(string="Code", index=True)