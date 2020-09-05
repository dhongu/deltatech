# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
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
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp


class mail_automatically(models.Model):
    _name = 'mail.automatically'
    _description = "Automatically Mail"

    partner_ids = fields.Many2many('res.partner', 'mail_automatically_partener_rel', 'mail_automatically_id', 'partner_id',
                                   string='Recipients', help="List of partners that will be added as follower of the current document.")

    type = fields.Selection([('picking', 'Stock Picking'), ('invoice', 'Account Invoice')], string='Type')

    picking_type_id = fields.Many2one('stock.picking.type', string='Picking Type')

    journal_id = fields.Many2one('account.journal', string='Journal')

    subject = fields.Char(string='Subject')
    message = fields.Html(string='Message')


class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def send_automatically_mail(self):
        for picking in self:
            mail_auto = self.env['mail.automatically'].search(
                [('type', '=', 'picking'), ('picking_type_id', '=', picking.picking_type_id.id)])
            if mail_auto:
                # de eliminat utilizatorii care deja sunt in list ????
                new_follower_ids = [p.id for p in mail_auto.partner_ids]
                picking.message_subscribe(new_follower_ids)
                message = self.env['mail.message'].with_context({'default_starred': True}).create({
                    'model': 'stock.picking',
                    'res_id': picking.id,
                    'record_name': picking.name_get()[0][1],
                    'email_from': self.env['mail.message']._get_default_from(),
                    'reply_to': self.env['mail.message']._get_default_from(),
                    'subject': mail_auto.subject or '',
                    'body': mail_auto.message or mail_auto.subject,
                    'message_id': self.env['mail.message']._get_message_id({'no_auto_thread': True}),
                    'partner_ids': [(4, id) for id in new_follower_ids],
                })

    @api.cr_uid_ids_context
    def do_transfer(self, cr, uid, picking_ids, context=None):
        res = super(stock_picking, self).do_transfer(cr, uid, picking_ids, context)
        self.send_automatically_mail(cr, uid, picking_ids, context)
        return res


class account_invoice(models.Model):
    _inherit = "account.invoice"

    @api.multi
    def invoice_validate(self):
        res = super(account_invoice, self).invoice_validate()
        for invoice in self:
            mail_auto = self.env['mail.automatically'].search(
                [('type', '=', 'invoice'), ('journal_id', '=', invoice.journal_id.id)])
            if mail_auto:
                new_follower_ids = [p.id for p in mail_auto.partner_ids]
                invoice.message_subscribe(new_follower_ids)
                message = self.env['mail.message'].with_context({'default_starred': True}).create({
                    'model': 'account.invoice',
                    'res_id': invoice.id,
                    'record_name': invoice.name_get()[0][1],
                    'email_from': self.env['mail.message']._get_default_from(),
                    'reply_to': self.env['mail.message']._get_default_from(),
                    'subject': mail_auto.subject or '',
                    'body': mail_auto.message or mail_auto.subject,
                    'message_id': self.env['mail.message']._get_message_id({'no_auto_thread': True}),
                    'partner_ids': [(4, id) for id in new_follower_ids],
                })
        return res


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
