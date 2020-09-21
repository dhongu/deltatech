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

from odoo import models, fields, api, tools, _ , SUPERUSER_ID
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.api import Environment
 


class mail_compose_message(models.TransientModel):
    _inherit = 'mail.compose.message'

    only_selected = fields.Boolean(string="Send only for selected users")
    auto_subscribe = fields.Boolean(string="Subscribe Recipients", default=True)
    mail_notify_noemail = fields.Boolean(string="Only internal notification", help="It will use internal Odoo mail without sending out email system")

    attachment_mode = fields.Boolean(string="List attachments")


    @api.onchange('only_selected')
    def onchange_only_selected(self):
        if self.only_selected and not self.partner_ids:
            #trebuie sa adaug partenerii interesati ca sa-i fie mai usor operatorului sa-i elimine
        
            message = self
    
            partners_to_notify = set([])
            subtype_id = self.env.ref('mail.mt_comment')
            # all followers of the mail.message document have to be added as partners and notified if a subtype is defined (otherwise: log message)
            if message.model and message.res_id:
                
                # browse as SUPERUSER because rules could restrict the search results
                fol_ids = self.env["mail.followers"].sudo().search( [ ('res_model', '=', message.model),('res_id', '=', message.res_id)])
                partners_to_notify |= set(  fo.partner_id.id for fo in fol_ids  if subtype_id.id in [st.id for st in fo.subtype_ids]  )
                
            # remove me from notified partners, unless the message is written on my own wall
            if message.author_id and message.model == "res.partner" and message.res_id == message.author_id.id:
                partners_to_notify |= set([message.author_id.id])
            elif message.author_id:
                partners_to_notify -= set([message.author_id.id])
    
            # all partner_ids of the mail.message have to be notified regardless of the above (even the author if explicitly added!)
            if message.partner_ids:
                partners_to_notify |= set([p.id for p in message.partner_ids])
            
            self.partner_ids =  self.env['res.partner'].browse(partners_to_notify )    
        
            
    @api.model
    def default_get(self, fields):
        defaults = super(mail_compose_message, self).default_get(fields)
        # poate ar fi bine daca fac un tabel cu modelele la care trmiterea de emai sa se faca
        res_model = defaults.get('model',False)
        if res_model and res_model == 'mail.group':
            defaults['mail_notify_noemail'] = False
        else:
            defaults['mail_notify_noemail'] =  eval(self.env['ir.config_parameter'].sudo().get_param( key="mail.notify.noemail", default="False"))
        # poate ca documentele anexate trebuie sa fie in functie de o configurare ??
        """
        res_id = defaults.get('res_id',False)   
        if res_model and res_id:
            attachment_ids = self.env['ir.attachment'].search([('res_model', '=',  res_model), 
                                                               ('res_id', '=', res_id)])
            defaults['attachment_ids'] =     [(6, False, attachment_ids.ids)]
        """

        return defaults
    
    def send_mail(self, cr, uid, ids, context=None):
        """ Process the wizard content and proceed with sending the related
            email(s), rendering any template patterns on the fly if needed. """
        context = dict(context or {})
        
        for wizard in self.browse(cr, uid, ids, context):
            context['mail_post_autofollow'] = wizard.auto_subscribe
            context['only_selected'] = wizard.only_selected
            context['mail_notify_noemail'] = wizard.mail_notify_noemail
            
        return super(mail_compose_message, self).send_mail(cr, uid, ids, context)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:





