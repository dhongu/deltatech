# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


import odoo.addons.decimal_precision as dp

from odoo import models, fields


class product_template(models.Model):
    _inherit = 'product.template'

    dimensions = fields.Char(string='Dimensions')
    shelf_life = fields.Float(string='Shelf Life', digits=dp.get_precision('Product UoM'))
    uom_shelf_life = fields.Many2one('uom.uom', string='Unit of Measure Shelf Life',
                                     help="Unit of Measure for Shelf Life", group_operator="avg")

    manufacturer = fields.Many2one('res.partner', string='Manufacturer', domain=[('is_manufacturer', '=', True)])

