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

 



class mail_message(models.Model):
    _inherit = 'mail.message' 

    


    # deschiderea unui document nu duce si la marcarea ca fiind citit
    @api.cr_uid_ids_context
    def set_message_read(self, cr, uid, msg_ids, read, create_missing=True, context=None):
        mail_read_set_read = context.get('mail_read_set_read',False)
        if mail_read_set_read:
            open_set_read =  eval(self.pool['ir.config_parameter'].get_param(cr, uid, "mail.open.set.read", default="False", context=context))
            if not open_set_read:
                return
        return super(mail_message,self).set_message_read( cr, uid, msg_ids, read, create_missing, context)


    def _notify(self, cr, uid, newid, context=None, force_send=False, user_signature=True):
        """ Add the related record followers to the destination partner_ids if is not a private message.
            Call mail_notification.notify to manage the email sending
        """
        if context and context.get('only_selected',False):
            message = self.browse(cr, SUPERUSER_ID, newid, context=context)
            if message.subtype_id:
                self.write(cr, SUPERUSER_ID, newid, {'subtype_id':False} , context=context)
        if 'mail_notify_noemail' in context:
            message = self.browse(cr, SUPERUSER_ID, newid, context=context)
            if message.type == 'comment':
                if context['mail_notify_noemail']: 
                    self.write(cr, SUPERUSER_ID, newid, {'type':'notification'} , context=context)
                else:
                    self.write(cr, SUPERUSER_ID, newid, {'type':'email'} , context=context)
                    
        return super(mail_message,self)._notify( cr, uid, newid, context, force_send, user_signature)
        
class mail_notification(models.Model):
    _inherit = 'mail.notification'

    @api.model
    def get_link(self, model ):
        for model_id, model_name in model.name_get():
            link = "<a href='#id=%s&model=%s'>%s</a>" % (str(model_id), model._name, model_name )
        return link
    
    @api.multi
    def web_notification(self,message_id):
        message = self.env['mail.message'].sudo().browse( message_id )

        # compute partners
        
        notify_pids = []
        for notification in self:
            if notification.is_read:
                continue
            partner = notification.partner_id
            # Do not send to partners having same email address than the author (can cause loops or bounce effect due to messy database)
            if message.author_id and message.author_id.email == partner.email:
                continue

            notify_pids.append(partner.id)
            
 
        
        if not notify_pids:
            return True
        
        users = self.env['res.users'].search([('partner_id','in',notify_pids)])   
        for user in  users:   
            link = "<a href='#id=%s&model=%s'>%s</a>" % (str(message.res_id), message.model, message.record_name )
            title = _('New message in the document: %s') % link
            user.post_notification(title=title,message=message.subject or ' ')        


    # nu se mai trimit toate notificarile si pe email
    
    def _notify(self, cr, uid, message_id, partners_to_notify=None, context=None, force_send=False, user_signature=True):
        if context is None:
            context = {}  
         
        context = context.copy() 

        if not 'mail_notify_noemail' in context:         
            mail_notify_noemail =  eval(self.pool['ir.config_parameter'].get_param(cr, SUPERUSER_ID, "mail.notify.noemail", default="False", context=context))
                 
            context['mail_notify_noemail'] = mail_notify_noemail
        
        #print 'mail_notify_noemail', context['mail_notify_noemail'], type(context['mail_notify_noemail'])
            
        res = super(mail_notification,self)._notify( cr, uid,  message_id, partners_to_notify, context)
        ids = self.search(cr, SUPERUSER_ID, [('message_id', '=', message_id), ('partner_id', 'in', partners_to_notify)], context=context)
        self.web_notification( cr, SUPERUSER_ID, ids, message_id, context=context)
        return res

    
    """
    def _notify_email(self, cr, uid, ids, message_id, force_send=False, user_signature=True, context=None):
        self.web_notification( cr, uid, ids, message_id, context=context)
        return super(mail_notification,self)._notify_email( cr, uid, ids, message_id, force_send, user_signature, context)
    """
    
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:





