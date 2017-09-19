# -*- coding: utf-8 -*-


from odoo import api
from odoo import models, fields, api
from odoo.tools import float_compare


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    consolidation = fields.Char(string='Consolidation')