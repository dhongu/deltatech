# -*- coding: utf-8 -*-
# ©  2017 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _

from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_TIME_FORMAT
import time
from datetime import datetime


class sale_order_line(models.Model):
    _inherit = "sale.order.line"

    # # pretul de achizitie in moneda documentului
    # todo: de actualizat acest pret cu valaorea produsului in momentul livarii
    # purchase_price = fields.Float(string='Cost Price', digits='Product Price',
    #                              compute="_compute_purchase_price", store=True)

    @api.depends('product_id')
    def _compute_purchase_price(self):
        for line in self:
            line.purchase_price = line._compute_margin(line.order_id, line.product_id, line.product_uom)

    def change_price_or_product(self, res):
        if not res.get('warning', False):
            if self.price_unit < self.purchase_price and self.purchase_price > 0:
                warning = {
                    'title': _('Price Error!'),
                    'message': _('Do not sell below the purchase price.'),
                }
                res['warning'] = warning
        return res

    @api.onchange('product_id')
    def product_id_change(self):
        res = super(sale_order_line, self).product_id_change()
        res = self.change_price_or_product(res)
        return res

    @api.onchange('price_unit')
    def price_unit_change(self):
        res = {}
        res = self.change_price_or_product(res)
        return res

    @api.constrains('price_unit', 'purchase_price')
    def _check_sale_price(self):
        if self.price_unit < self.purchase_price:
            if not self.env['res.users'].has_group('deltatech_sale_margin.group_sale_below_purchase_price'):
                raise Warning(_('You can not sell below the purchase price.'))
            else:
                message = _('Sale %s under the purchase price.') % self.product_id.name
                self.order_id.message_post(body=message)
