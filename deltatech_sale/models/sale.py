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

        return super(SaleOrderLine, self).product_id_change()

