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



from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_TIME_FORMAT
import time
from datetime import datetime


class sale_order_line(models.Model):
    _inherit = "sale.order.line"

    # pretul de achizitie in moneda documentului
    purchase_price = fields.Float(string='Cost Price', digits=dp.get_precision('Product Price'),
                                  compute="_compute_purchase_price", store=True)

    @api.one
    @api.depends('product_id')
    def _compute_purchase_price(self):
        frm_cur = self.env.user.company_id.currency_id
        to_cur = self.order_id.currency_id
        if self.product_id:
            purchase_price = self.product_id.standard_price
            to_uom = self.product_uom.id
            if to_uom != self.product_id.uom_id.id:
                purchase_price = self.env['product.uom']._compute_price(self.product_id.uom_id.id, purchase_price,
                                                                        to_uom)

            self.purchase_price = frm_cur.with_context(date=self.order_id.date_order).compute(purchase_price, to_cur,
                                                                                              round=False)
        else:
            self.purchase_price = 0

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(sale_order_line, self).product_id_change()

        if not res['value'].get('warning', False):
            if 'price_unit' in res['value'] and 'purchase_price' in res['value']:
                if res['value']['price_unit'] < res['value']['purchase_price'] and res['value']['purchase_price'] > 0:
                    warning = {
                        'title': _('Price Error!'),
                        'message': _('You can not sell below the purchase price.'),
                    }
                    res['warning'] = warning
        return res

    @api.multi
    @api.onchange('price_unit')
    def price_unit_change(self):
        res = {}

        if self.price_unit < self.purchase_price and self.purchase_price > 0:
            warning = {
                'title': _('Price Error!'),
                'message': _('You can not sell below the purchase price.'),
            }
            res['warning'] = warning
        return res

    @api.one
    @api.constrains('price_unit', 'purchase_price')
    def _check_sale_price(self):
        if not self.env['res.users'].has_group('deltatech_sale_margin.group_sale_below_purchase_price'):
            if self.price_unit < self.purchase_price:
                raise Warning(_('You can not sell below the purchase price.'))


    """ nu mai cred ca e nevoie in 10 de ea
    @api.multi
    def write(self, values):
        if 'product_id' in values and 'price_unit' not in values:
            order = self[0].order_id
            order.product_id_change()
            '''
            defaults = self.product_id_change(pricelist=order.pricelist_id.id,
                                              product=values.get('product_id', self.product_id.id),
                                              qty=float(values.get('product_uom_qty', self[0].product_uom_qty)),
                                              uom=values.get('product_uom',
                                                             self[0].product_uom.id if self[0].product_uom else False),
                                              qty_uos=float(values.get('product_uos_qty', self[0].product_uos_qty)),
                                              uos=values.get('product_uos',
                                                             self[0].product_uos.id if self[0].product_uos else False),
                                              name=values.get('name', False),
                                              partner_id=order.partner_id.id,
                                              date_order=order.date_order,
                                              fiscal_position=order.fiscal_position.id if order.fiscal_position else False,
                                              )
            '''
            values['price_unit'] = order.price_unit

        return super(sale_order_line, self).write(values)
    """

