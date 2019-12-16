# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
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

import odoo.addons.decimal_precision as dp

from odoo import api, models, fields


class product_template(models.Model):
    _inherit = 'product.template'

    dimensions = fields.Char(string='Dimensions')
    shelf_life = fields.Float(string='Shelf Life', digits=dp.get_precision('Product UoM'))
    uom_shelf_life = fields.Many2one('product.uom', string='Unit of Measure Shelf Life',
                                     help="Unit of Measure for Shelf Life", group_operator="avg")

    manufacturer = fields.Many2one('res.partner', string='Manufacturer', domain=[('is_manufacturer', '=', True)])

    def set_manufacturer(self, manufacturer):
        if isinstance(manufacturer, int):
            manufacturer = self.env['res.partner'].browse(manufacturer)
            manufacturer = manufacturer.name
        manufacturer_att = self.env['product.attribute'].search([('name', '=ilike', 'manufacturer')])
        if not manufacturer_att:
            manufacturer_att = self.env['product.attribute'].create({'name': 'manufacturer', 'create_variant': False})

        domain = [('name', '=ilike', manufacturer), ('attribute_id', '=', manufacturer_att.id)]
        manufacturer_value = self.env['product.attribute.value'].search(domain)
        if not manufacturer_value:
            manufacturer_value = self.env['product.attribute.value'].create({
                'name': manufacturer,
                'attribute_id': manufacturer_att.id
            })

        attribute_line = False
        for line in self.attribute_line_ids:
            if line.attribute_id == manufacturer_att:
                attribute_line = line

        if not attribute_line:
            attribute_line = self.env['product.attribute.line'].create({
                'attribute_id': manufacturer_att.id,
                'product_tmpl_id': self.id
            })

        attribute_line.write({'value_ids': [(6,0, [manufacturer_value.id])]})

    # @api.multi
    # def write(self, vals):
    #     from_attribute_value = self.env.context.get('from_attribute_value',False)
    #     if not from_attribute_value and 'manufacturer' in vals:
    #         for prod in self:
    #             prod.set_manufacturer(vals['manufacturer'])
    #     return super(product_template, self).write(vals)



class ProductAttributeLine(models.Model):
    _inherit = "product.attribute.line"


    # @api.model
    # def create(self, vals):
    #     res = super(ProductAttributeLine, self).create(vals)
    #     res.set_manufacturer()
    #     return res
    #
    # @api.multi
    # def write(self, vals):
    #     res = super(ProductAttributeLine, self).write(vals)
    #     self.set_manufacturer()
    #     return res

    @api.multi
    def set_manufacturer(self):
        for line in self:
            if line.value_ids:
                manufacturer_partner = line.value_ids.set_manufacturer()
                if manufacturer_partner:
                    line.product_tmpl_id.with_context(from_attribute_value=True).write({'manufacturer' : manufacturer_partner.id})


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"


    # @api.model
    # def create(self, vals):
    #     res = super(ProductAttributeValue, self).create(vals)
    #     res.set_manufacturer()
    #     return res

    @api.multi
    def set_manufacturer(self):
        manufacturer_partner = False
        manufacturer_att = self.env['product.attribute'].search([('name', '=ilike', 'manufacturer')])
        if not manufacturer_att:
            manufacturer_att = self.env['product.attribute'].create({'name': 'manufacturer', 'create_variant': False})

        from_attribute_value = self.env.context.get('from_attribute_value', False)
        if not from_attribute_value:
            for val in self:
                if val.attribute_id == manufacturer_att:
                    manufacturer_name = val.name
                    manufacturer_partner = self.env['res.partner'].search([('name', '=ilike', manufacturer_name)],limit=1)
                    if not manufacturer_partner:
                        manufacturer_partner = self.env['res.partner'].create({
                            'name': manufacturer_name,
                            'is_manufacturer': True
                        })
                    val.product_ids.with_context(from_attribute_value=True).write({'manufacturer': manufacturer_partner.id})

        return manufacturer_partner


    # @api.multi
    # def write(self, vals):
    #     res = super(ProductAttributeValue, self).write(vals)
    #     self.set_manufacturer()
    #     return res



