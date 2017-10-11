# -*- coding: utf-8 -*-




from odoo import models, fields, api, _


class Picking(models.Model):
    _inherit = "stock.picking"

    city = fields.Char(related="partner_id.city", string="City", store=True)
    state_id = fields.Many2one('res.country.state', related="partner_id.state_id", string="State", store=True)

