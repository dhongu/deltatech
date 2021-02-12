# -*- coding: utf-8 -*-

from openerp import models, fields, api, _


class stock_loc_reval(models.TransientModel):
    _name = 'stock_loc_reval'
    _description = "Location Revaluation"

    location_id = fields.Many2one('stock.location')
