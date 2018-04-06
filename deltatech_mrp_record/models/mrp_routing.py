# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _



class MrpRoutingWorkcenter(models.Model):
    _inherit = 'mrp.routing.workcenter'

    code = fields.Char(string="Code", index=True)