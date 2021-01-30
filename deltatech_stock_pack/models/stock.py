# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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
from openerp.exceptions import except_orm, Warning, RedirectWarning, ValidationError
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp
from dateutil.relativedelta import relativedelta
from datetime import datetime, date, timedelta
import logging

_logger = logging.getLogger(__name__)


class stock_move(models.Model):
    _inherit = "stock.move"

    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        res = super(stock_move, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=context)
        packs = {}
        for quant in move.quant_ids:
            if quant.qty > 0:
                key = str(int(quant.qty))
                if not key in packs:
                    packs[key] = 1
                else:
                    packs[key] += 1
        pack_str = ''

        for key in packs:
            pack_str += str(packs[key]) + ' x ' + str(key) + ';'  # + move.product_uom.name +'; '
        res['name'] += '\n' + pack_str
        if inv_type in ('out_invoice', 'out_refund') and move.procurement_id and move.procurement_id.sale_line_id:
            sale_line = move.procurement_id.sale_line_id
            if sale_line.order_id.client_order_ref:
                str_date = fields.Datetime.from_string(sale_line.order_id.date_order).strftime('%d-%m-%Y')

                res['name'] += '\n' + _('Ord.') + sale_line.order_id.client_order_ref + '/' + str_date

                ## sale_line.order_id.date_order[:10]  # oare ce e asta ?
        return res


class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def do_transfer(self):

        res = super(stock_picking, self).do_transfer()
        package = self.env['stock.quant.package']
        for picking in self:
            for operation in picking.pack_operation_ids:
                package |= operation.result_package_id
            # for move in picking.move_lines:
            #     for quant in move.quant_ids:
            #         package |= quant.package_id
        package.action_get_components()
        return res


class stock_package(models.Model):
    _inherit = "stock.quant.package"

    volume = fields.Float('Volume', help="The volume in m3.")
    weight = fields.Float('Gross Weight', digits=dp.get_precision('Stock Weight'), help="The gross weight in Kg.")
    weight_net = fields.Float('Net Weight', digits=dp.get_precision('Stock Weight'), help="The net weight in Kg.")

    # componente utilizate in acest pachet:

    bom_id = fields.Many2one('package.bom', 'Bill of Materials')

    component_ids = fields.One2many('stock.quant.package.component', 'package_id', string='Components')

    @api.multi
    def action_get_components(self):
        self.compute_components(raise_if_not_found=False) # sa nu mai dea eroare  in mod implicti

    @api.multi
    def compute_components(self, raise_if_not_found=False):
        categ_all = self.env.ref('product.product_category_all')

        for package in self.filtered(lambda x: not x.bom_id):
            categ = False
            bom = False
            product = self.env['product.product']
            for quant in package.quant_ids:
                product = quant.product_id
                categ = product.categ_id

            if not product:
                return
            if not categ or categ.id == categ_all.id:
                categ = self.generate_category(product)

            if categ:
                bom = self.env['package.bom'].search([('categ_id', '=', categ.id)], limit=1)
                if not bom:
                    bom = self.env['package.bom'].search([('name', 'like', categ.name)], limit=1)

            if bom:
                package.write({'bom_id': bom.id})
            else:
                if raise_if_not_found:
                    raise ValidationError('Nu se poate determina lista de matriale pentru %s' % product.categ_id.name)

        for package in self.filtered(lambda x: x.bom_id):
            qty = 0
            for quant in package.quant_ids:
                qty += quant.qty
            coef = qty / package.bom_id.product_qty
            package.component_ids.unlink()
            for item in package.bom_id.bom_line_ids:
                self.env['stock.quant.package.component'].create({
                    'package_id': package.id,
                    'product_id': item.product_id.id,
                    'product_qty': item.product_qty * coef
                })

    def generate_category(self, product):
        categ = False
        if product.default_code:
            code = product.default_code.split(' ')[0]
            categ = self.env['product.category'].search([('name', '=', code)], limit=1)
            if not categ:
                categ = self.env['product.category'].create({'name': code})
            product.write({'categ_id': categ.id})
        return categ

    @api.multi
    def get_components(self):
        categ_all = self.env.ref('product.product_category_all')

        components = {'by_component': {}, 'by_categ': {}, 'by_product': {}}
        for pack in self:
            qty = 0.0

            for quant in pack.quant_ids:
                categ = quant.product_id.categ_id
                product = quant.product_id
                if categ.id == categ_all.id:
                    categ = self.generate_category(product)
                qty += quant.qty

            if not categ:
                continue

            if categ.id not in components['by_categ']:
                components['by_categ'][categ.id] = {'categ': categ, 'qty': qty, 'components': {}}
            else:
                components['by_categ'][categ.id]['qty'] += qty
            if product.id not in components['by_product']:
                components['by_product'][product.id] = {'product': product, 'qty': qty, 'components': {}}
            else:
                components['by_product'][product.id]['qty'] += qty

            by_categ = components['by_categ'][categ.id]['components']
            by_product = components['by_product'][product.id]['components']
            by_component = components['by_component']

            if not pack.component_ids:
                pack.compute_components()
            # else:
            #     # recalculez
            #     pack.compute_components()

            for comp in pack.component_ids:
                if comp.product_id.id not in by_categ:
                    by_categ[comp.product_id.id] = {'component': comp.product_id, 'qty': 0.0}
                by_categ[comp.product_id.id]['qty'] += comp.product_qty

                if comp.product_id.id not in by_product:
                    by_product[comp.product_id.id] = {'component': comp.product_id, 'qty': 0.0}
                by_product[comp.product_id.id]['qty'] += comp.product_qty

                if comp.product_id.id not in by_component:
                    by_component[comp.product_id.id] = {'component': comp.product_id, 'qty': 0.0}
                by_component[comp.product_id.id]['qty'] += comp.product_qty

        print (components)
        return components


class stock_package_component(models.Model):
    _name = "stock.quant.package.component"

    package_id = fields.Many2one('stock.quant.package')
    product_id = fields.Many2one('product.product')
    categ_id = fields.Many2one('product.category', related='product_id.categ_id')
    product_qty = fields.Float('Component Quantity', required=True)
    product_uom = fields.Many2one('product.uom', related='product_id.uom_id', readonly=True)
