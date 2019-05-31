# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError



class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'


    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):

        if not self.order_id.partner_id:
            raise UserError(_('Before choosing a product,\n select a customer in the sales form.'))

        result = super(SaleOrderLine, self).product_id_change()

        message = ''
        if self.product_id:
            if self.product_id.standard_price == 0:
                message += _('Cost price is zero')
            if self.price_unit < self.product_id.standard_price:
                message += _('You can not sell below the purchase price.')


        if message:
            if 'warning' in result:
                result['warning']['message'] += message
            else:
                result['warning'] = {'message':message}

        return result

