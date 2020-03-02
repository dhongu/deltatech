# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import api, models, fields, _, tools


class product_category(models.Model):
    _inherit = 'product.category'
    cost_categ = fields.Selection([('raw', 'Raw materials'),
                                   ('semi', 'Semi-products'),
                                   ('pak', 'Packing Material'),
                                   ], string='Cost Category')
