# coding=utf-8


from odoo import models, fields, api, _


class MrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'
    _rec_name = "name"

    to_cat = fields.Boolean(string="To Cut")


