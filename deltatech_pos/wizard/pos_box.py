# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.addons.point_of_sale.wizard.pos_box import PosBox
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import base64
from io import StringIO

"""
Introducere numerar in sertar :
I,1,______,_,__;0;10<suma>;;;;

Retragere numerar din sertar :
I,1,______,_,__;1;10<suma>;

"""


class PosBoxIn(PosBox):
    _inherit = 'cash.box.in'

    file_name = fields.Char(string='File Name')
    data_file = fields.Binary(string='File')

    @api.multi
    def do_download_file(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=%s&download=True&field=data_file&id=%s&filename=%s' % (
            self._name, self.id, self.file_name),
            'target': 'self',
        }

    @api.multi
    def run(self):
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', [])
        res = super(PosBoxIn, self).run()

        if active_model == 'pos.session':
            session = self.env[active_model].browse(active_ids)
            amount = self.amount
            amount = -amount if amount > 0.0 else amount
            data_file = ''
            data_file += 'I,1,______,_,__;0;%s;;;;\r\n' % amount
            data_file +='P,1,______,_,__;%s;;;;\r\n' % self.ref
            data_file = base64.encodestring(data_file.encode())
            self.write({'data_file': data_file, 'file_name': 'cash_box_in.inp'})

            res = self.do_download_file()
        return res


class PosBoxOut(PosBox):
    _inherit = 'cash.box.out'

    @api.multi
    def do_download_file(self):
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content?model=%s&download=True&field=data_file&id=%s&filename=%s' % (
                self._name, self.id, self.file_name),
            'target': 'self',
        }

    @api.multi
    def run(self):
        active_model = self.env.context.get('active_model', False)
        active_ids = self.env.context.get('active_ids', [])
        res = super(PosBoxOut, self).run()

        if active_model == 'pos.session':
            session = self.env[active_model].browse(active_ids)
            amount = self.amount
            amount = -amount if amount > 0.0 else amount
            data_file = ''
            data_file += 'I,1,______,_,__;1;%s;;;;\r\n' % amount
            data_file += 'P,1,______,_,__;%s;;;;\r\n' % self.ref
            data_file = base64.encodestring(data_file.encode())
            self.write({'data_file': data_file, 'file_name': 'cash_box_out.inp'})

            res = self.do_download_file()
        return res
