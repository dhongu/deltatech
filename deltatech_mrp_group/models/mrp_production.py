# -*- coding: utf-8 -*-


from odoo import api
from odoo import models, fields, api
from odoo.tools import float_compare



class SaleOrder(models.Model):
    _inherit = "sale.order"

    consolidation = fields.Char(string='Consolidation')