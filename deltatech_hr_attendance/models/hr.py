# coding=utf-8



from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp

class Department(models.Model):
    _inherit = "hr.department"

    type = fields.Selection([('div', 'Division'),('dep','Department'),('for','Formation')])
