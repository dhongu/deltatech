# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    parameter_value_ids = fields.One2many('mrp.parameter.value', 'product_id', string='Parameter')