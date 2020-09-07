# -*- coding: utf-8 -*-


from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import Warning, RedirectWarning


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    address = fields.Many2one('res.partner', string="Address")
