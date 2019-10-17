# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _



class company(models.Model):
    _inherit = 'res.company'

    watermark_image  = fields.Binary(string='Watermark image')


