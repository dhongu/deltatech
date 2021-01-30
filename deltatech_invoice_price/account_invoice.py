# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015-2019 Deltatech All Rights Reserved
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
import openerp.addons.decimal_precision as dp
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_TIME_FORMAT
import time
from datetime import datetime


class account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def invoice_validate(self):
        res = super(account_invoice, self).invoice_validate()
        self.update_sale_price()
        return res

    @api.multi
    def update_sale_price(self):
        for invoice in self.filtered(lambda r: r.type == 'out_invoice'):
            for line in invoice.invoice_line:
                sale_line = self.env['sale.order.line'].search([('invoice_lines', '=', line.id)])
                if sale_line and sale_line.order_id.currency_id == invoice.currency_id and sale_line.price_unit != line.price_unit:
                    msg = _('Pretul pentru %s a fost actualizat de la %s la %s conform facturii ') % (
                                    line.product_id.name, sale_line.price_unit, line.price_unit)
                    sale_line.order_id.message_post(body=msg)
                    sale_line.write({'price_unit': line.price_unit})
