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

import base64
import contextlib
import cStringIO

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp

try:
    import html2text
except:
    from odoo.addons.mail.models import html2text


class account_invoice_export_bf(models.TransientModel):
    _name = 'account.invoice.export.bf'
    _description = "Export Datecs"

    name = fields.Char(string='File Name', readonly=True)
    data_file = fields.Binary(string='File', readonly=True)
    text_data = fields.Text(string="Text", readonly=True)
    invoice_id = fields.Many2one('account.invoice')
    
    @api.model
    def default_get(self, fields):
        defaults = super(account_invoice_export_bf, self).default_get(fields)

        active_id = defaults.get('invoice_id', self.env.context.get('active_id', False))

        if active_id:
            invoice_id = self.env['account.invoice'].browse(active_id)
            defaults['invoice_id'] = invoice_id.id

        if not invoice_id or invoice_id.type != 'out_invoice':
            raise Warning(_('Please select Customer Invoice %s') % invoice_id.name)

        if not invoice_id.payment_ids:
            raise Warning(_('Invoice %s is not paid') % invoice_id.name)

        # generare fisier pentru casa de marcat OPTIMA CR1020
        currency = invoice_id.currency_id or None
        with contextlib.closing(cStringIO.StringIO()) as buf:
            
            # printing reference
            buf.write('2;%s\r\n' % _('Ref:'+invoice_id.number))
            # initial values for negative total test
            negative_price = 0.0
            total_price = 0.0;
            for line in invoice_id.invoice_line_ids:

                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = False
                if line.invoice_line_tax_ids:
                    taxes = line.invoice_line_tax_ids.compute_all(price, currency, 1,
                                                                  product=line.product_id,
                                                                  partner=line.invoice_id.partner_id)
                price = taxes['total_included']
                
                # if value <0, add to to discount
                if price < 0 or line.quantity < 0:
                    #raise Warning(_('Price can not be negative '))
                    negative_price += price*line.quantity
                
                # if value > 0, print position
                if price >= 0 and line.quantity >= 0:
                    # split name in 18-chars array
                    prod_name = line.product_id.name.replace('\n', ' ')
                    prod_name_array = []
                    for start in range(0,len(prod_name),18):
                        prod_name_array.append(prod_name[start:start+18])
                    
                    prod_name = prod_name_array[0]
                    buf.write('1;%s;1;1;%s;%s\r\n' % (prod_name,
                                                           str(int(price * 100.0)),
                                                           str(int(line.quantity * 100000.0))))
                    if(len(prod_name_array)) > 1:
                        for extra_lines in prod_name_array[1:len(prod_name_array)]:
                            buf.write('2;%s\r\n' % extra_lines)
                    total_price += price*line.quantity
             
            # if total value is negaive        
            if total_price + negative_price < 0:
                raise Warning(_('Nu se poate emite bon cu valoare negativa!!!'))
                
            # if discount exists, print it   
            if negative_price < 0:
                negative_price = -negative_price
                negative_price = negative_price*100
                negative_price_string = str(int(negative_price))
                buf.write('7;1;1;1;0;%s;1\r\n' % negative_price_string)
            
            # print payments
            for payment in invoice_id.payment_ids:
                #if payment.payment_method_code == 'manual':
                if payment.journal_id.type == 'cash':
                    buf.write('5;%s;1;1;0\r\n' % str(int(payment.amount * 100.0)))
                else:
                    buf.write('5;%s;3;1;0\r\n' % str(int(payment.amount * 100.0)))

            defaults['text_data'] = buf.getvalue()
            out = base64.encodestring(buf.getvalue())

        filename = 'ONLINE_' + invoice_id.number
        filename = "".join(i for i in filename if i not in "\/:*?<>|")

        extension = 'TXT'

        defaults['name'] = "%s.%s" % (filename, extension)
        defaults['data_file'] = out

        return defaults

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
