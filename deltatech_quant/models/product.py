

from odoo import models, fields, api

class product_template(models.Model):
    _inherit = 'product.template'

    manufacturer = fields.Many2one('res.partner', string='Manufacturer')  