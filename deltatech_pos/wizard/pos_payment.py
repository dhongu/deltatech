# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
import base64

class PosMakePayment(models.TransientModel):
    _inherit = 'pos.make.payment'

    @api.multi
    def check(self):
        res = super(PosMakePayment, self).check()
        return self.print_bf_out()


    def print_bf_out(self):
        order = self.env['pos.order'].browse(self.env.context.get('active_id', False))

        if order.config_id.ecr_type == 'datecs18':
            com_print = 'P,1,______,_,__;%s;;;;\r\n'
            com_out = 'I,1,______,_,__;1;%s;;;;\r\n'
        elif order.config_id.ecr_type == 'optima':
            com_print = "2;%s\r\n"
            com_out = "2;%s\r\n"


        type = 'out'

        txt1 = _('Payment disposal')
        txt2 = _('It was paid to:')
        if order.partner_id:
            txt2 += order.partner_id.name
        else:
            txt2 += '__________'

        txt3 = ''

        if order.partner_id:
            txt3 += order.partner_id.name
        else:
            txt3 = '__________'
        txt3 += '          ' + self.env.user.name

        amount = self.amount
        amount = -amount if amount < 0.0 else amount
        data_file = ''
        data_file += com_out % amount
        data_file += com_print % ('%s :%s' % (txt1, order.name))
        data_file += com_print % '---------------------------------------'
        data_file += com_print % txt2
        data_file += com_print % (_('amount :%s') % amount)
        data_file += com_print % ('Ref :%s' % self.payment_name or '')
        data_file += com_print % '---------------------------------------'
        data_file += com_print % '---------------------------------------'

        data_file += com_print % _('I received,            I gave,')
        data_file += com_print % txt2

        data_file += com_print % '---------------------------------------'
        data_file += com_print % '---------------------------------------'
        data_file += com_print % '---------------------------------------'
        data_file += com_print % '---------------------------------------'
        data_file += com_print % '---------------------------------------'
        data_file = base64.encodestring(data_file.encode())

        ext = order.config_id.file_ext
        name = order.name.replace('/', '_')
        file_name = 'cash_box_%s_%s_%s.%s' % (name, type, self.id, ext)

        wizard = self.env['wizard.download.file'].create({'data_file': data_file,   'file_name': file_name} )

        return wizard.do_download_file()
