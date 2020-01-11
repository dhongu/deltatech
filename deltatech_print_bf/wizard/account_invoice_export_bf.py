# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import base64
import contextlib
from io import StringIO

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp

try:
    import html2text
except:
    from odoo.addons.mail.models import html2text

ecr_commands = {
    'optima': {
        'print': "2;{text}\r\n",
        'in': "2;%s\r\n",
        'out': "2;%s\r\n",
        'sale': '1;{name};1;1;{price};{qty}\r\n',  # comanda sale
        'total': '5;{amount};{type};1;0\r\n',  # comanda de inchidere
        'discount': '7;{type};1;1;0;{value};1\r\n',
        'amount': lambda value: value * 100,
        'qty': lambda value: value * 100000,
        'stl':'',
        'limit':18
    },

    'datecs': {
        'print': 'P,1,______,_,__;{text};;;;\r\n',
        'in': 'I,1,______,_,__;0;%s;;;;\r\n',
        'out': 'I,1,______,_,__;1;%s;;;;\r\n',
        'sale': 'S,1,______,_,__;{name};{price};{qty};{dep};{group};{tax};0;0;\r\n',  # comanda sale
        'total': 'T,1,______,_,__;{type};{amount};;;;\r\n',  # comanda de inchidere
        'discount': 'C,1,______,_,__;{type};{value};;;;\r\n',
        'amount': lambda value: round(value, 2),
        'qty': lambda value: round(value, 3),
        'stl':'',
        'limit':18
    },

    'datecs18': {
        'print': 'P,1,______,_,__;{text};;;;\r\n',
        'in': 'I,1,______,_,__;0;%s;;;;\r\n',
        'out': 'I,1,______,_,__;1;%s;;;;\r\n',
        'sale': 'S,1,______,_,__;{name};{price};{qty};{dep};{group};{tax};0;0;{uom};\r\n',  # comanda sale
        'total': 'T,1,______,_,__;{type};{amount};;;;\r\n',  # comanda de inchidere
        'discount': 'C,1,______,_,__;{type};{value};;;;\r\n',
        'amount': lambda value: round(value, 2),
        'qty': lambda value: round(value, 3),
        'stl':'L,1,______,_,__;\r\n',
        'limit':72
    },
}


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
        invoice_id = False
        active_id = defaults.get('invoice_id', self.env.context.get('active_id', False))

        if active_id:
            invoice_id = self.env['account.invoice'].browse(active_id)
            defaults['invoice_id'] = invoice_id.id

        if not invoice_id or invoice_id.type != 'out_invoice':
            raise Warning(_('Please select Customer Invoice %s') % invoice_id.name)

        if not  ( invoice_id.payment_ids  or invoice_id.state == 'paid') :
            raise Warning(_('Invoice %s is not paid') % invoice_id.name)

        # generare fisier pentru casa de marcat OPTIMA CR1020
        currency = invoice_id.currency_id or None

        ecr = self.env['ir.config_parameter'].sudo().get_param('account_invoice.ecr_type', 'datecs18')
        ecr_comm = ecr_commands[ecr]

        with contextlib.closing(StringIO()) as buf:

            # printing reference
            # buf.write('2;%s\r\n' % _('Ref:' + invoice_id.number))
            buf.write(ecr_comm['print'].format(text=_('Ref:' + invoice_id.number)))
            # initial values for negative total test
            negative_price = 0.0
            total_price = 0.0;
            for line in invoice_id.invoice_line_ids:

                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = False
                if line.invoice_line_tax_ids:
                    taxes = line.invoice_line_tax_ids.compute_all(price, currency,
                                                                  quantity=1,
                                                                  product=line.product_id,
                                                                  partner=line.invoice_id.partner_id)
                price = taxes['total_included']

                # if value <0, add to to discount
                if price < 0 or line.quantity < 0:
                    # raise Warning(_('Price can not be negative '))
                    negative_price += price * line.quantity

                # if value > 0, print position
                if price >= 0 and line.quantity >= 0:
                    # split name in 18-chars array
                    # todo: de pus un parametru in configuruare in functie de care sa se tipareasca codul produsului
                    prod_name = line.product_id.display_name.replace('\n', ' ')
                    prod_name_array = []
                    for start in range(0, len(prod_name), ecr_comm['limit']):
                        prod_name_array.append(prod_name[start:start + ecr_comm['limit']])

                    prod_name = prod_name_array[-1]

                    data = {
                        'name': prod_name,
                        'price': str(ecr_comm['amount'](price)),
                        'qty': str(ecr_comm['qty'](line.quantity)),
                        'dep': '1',
                        'group': '1',
                        'tax': '1',  # todo: de determinat codul de taxa
                        'uom': ''
                    }
                    if (len(prod_name_array)) > 1: # printing the first lines
                        for extra_lines in prod_name_array[0:len(prod_name_array)-1]:
                            buf.write(ecr_comm['print'].format(text=extra_lines))
                    buf.write(ecr_comm['sale'].format(**data))
                    # buf.write('1;%s;1;1;%s;%s\r\n' % (prod_name,
                    #                                   str(int(price * 100.0)),
                    #                                   str(int(line.quantity * 100000.0))
                    #                                   ))

                    total_price += price * line.quantity

            # if total value is negaive        
            if total_price + negative_price < 0:
                raise Warning(_('Nu se poate emite bon cu valoare negativa!!!'))

            # if discount exists, print it   
            if negative_price < 0:
                negative_price = -negative_price
                #negative_price = negative_price * 100
                negative_price_string =  str(ecr_comm['amount'](negative_price))
                # buf.write('7;1;1;1;0;%s;1\r\n' % negative_price_string)
                buf.write(ecr_comm['stl'])
                buf.write(ecr_comm['discount'].format(type='3', value=negative_price_string)) #discount valoric

            for payment in invoice_id.payment_ids:
                # if payment.payment_method_code == 'manual':
                if payment.journal_id.type == 'cash':
                    if payment.journal_id.code == 'VOUC' or payment.journal_id.code == "VOUPR":
                        buf.write(ecr_comm['print'].format(text=_('Voucher:') + payment.communication))

            # print payments
            for payment in invoice_id.payment_ids:
                # if payment.payment_method_code == 'manual':
                # if payment.journal_id.type == 'cash':
                #     if payment.journal_id.code == 'VOUC' or payment.journal_id.code == "VOUPR":
                #         buf.write('5;%s;5;1;0\r\n' % str(int(payment.amount * 100.0)))
                #     else:
                #         buf.write('5;%s;1;1;0\r\n' % str(int(payment.amount * 100.0)))
                # else:
                #     buf.write('5;%s;3;1;0\r\n' % str(int(payment.amount * 100.0)))

                if payment.state != 'draft':
                    data = {
                        'type': payment.journal_id.cod_ecr,
                        'amount': str(ecr_comm['amount'](payment.amount))
                    }
                    buf.write(ecr_comm['total'].format(**data))

            defaults['text_data'] = buf.getvalue()
            #out = base64.encodestring(buf.getvalue())
            out =  buf.getvalue()
            out = base64.b64encode(out.encode())

        filename = 'ONLINE_' + invoice_id.number
        filename = "".join(i for i in filename if i not in "\/:*?<>|")


        extension =  self.env['ir.config_parameter'].sudo().get_param('account_invoice.ecr_extension', 'inp')

        defaults['name'] = "%s.%s" % (filename, extension)
        defaults['data_file'] = out

        return defaults




