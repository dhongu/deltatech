# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2019 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import models, fields, api, _


class package_bom(models.Model):
    _name = "package.bom"
    _description =  'Bill of Materials'

    name = fields.Char(string="Name")
    categ_id = fields.Many2one('product.category', string='Category')
    product_qty = fields.Float('Product Quantity', required=True, default=100000)
    bom_line_ids = fields.One2many('package.bom.line', 'bom_id')

    @api.onchange('categ_id')
    def onchange_categ_id(self):
        self.name = self.categ_id.name


class package_bom_line(models.Model):
    _name = "package.bom.line"
    _description = 'Bill of Materials Line'

    bom_id = fields.Many2one('package.bom', ondelete='cascade')

    sequence = fields.Integer()
    product_id = fields.Many2one('product.product', string='Component')
    product_qty = fields.Float('Component Quantity', required=True)
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', readonly=True)
