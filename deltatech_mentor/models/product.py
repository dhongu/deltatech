# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError
from odoo.osv import expression

import odoo.addons.decimal_precision as dp


class ProductCategory(models.Model):
    _inherit = "product.category"

    tip_contabil = fields.Char('Simbol Tip Contabil')
    # gestiunea in care intra materialele la achizitie - nu este o abordare tocmai ok
    gestiune_mentor = fields.Char('Gestiune Mentor')

    way_production = fields.Selection([
        ('consumption', 'Consumption in production'),
        ('receipt', 'Receipt from production'),
        ('both', 'Consumption/Receipt')], default='', string='Production Way'
    )

    mentor_uom_id = fields.Many2one('uom.uom', string='Mentor UOM')
