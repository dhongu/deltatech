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

from openerp import models, fields, api, tools, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
from openerp.api import Environment




class send_invoice(models.TransientModel):
    """ Wizard to send invoice to partners and make them followers. """
    _name = 'send.invoice'
    _description = 'Send Invoice'


    partner_ids = fields.Many2many('res.partner', 'send_invoice_partener_rel', 'send_invoice_id','partner_id', 
                                      string='Recipients',help="List of partners that will be added as follower of the current document." )
    
    subject = fields.Char(string='Subject')
    message = fields.Html(string='Message')

 

    @api.multi
    def do_send(self):
        for wizard in self:
            active_ids = self.env.context.get('active_ids', [])       
            invoices = self.env['account.invoice'].browse(active_ids)
           
            for document in invoices: 
                new_follower_ids = [p.id for p in wizard.partner_ids]
                document.message_subscribe(new_follower_ids)
                 
                message = self.env['mail.message'].with_context({'default_starred':True}).create({
                    'model': 'account.invoice',
                    'res_id': document.id,
                    'record_name': document.name_get()[0][1],
                    'email_from': self.env['mail.message']._get_default_from( ),
                    'reply_to': self.env['mail.message']._get_default_from( ),
                    #'subject': _('Invoice %s') % ( document.name_get()[0][1]),
                    #'body': '%s' % wizard.message,
                    'subject': wizard.subject or '',
                    'body': wizard.message or wizard.subject,
                     
                    'message_id': self.env['mail.message']._get_message_id(  {'no_auto_thread': True} ),
                    'partner_ids': [(4, id) for id in new_follower_ids],
                    #'notified_partner_ids': [(4, id) for id in new_follower_ids]
                })
                


        return {'type': 'ir.actions.act_window_close'} 
    
 
     

    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:





