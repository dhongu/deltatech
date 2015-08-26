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




class mail_message(models.Model):
    _inherit = 'mail.message' 

    # deschiderea unui document nu duce si la marcarea ca fiind citit
    @api.cr_uid_ids_context
    def set_message_read(self, cr, uid, msg_ids, read, create_missing=True, context=None):
        mail_read_set_read = context.get('mail_read_set_read',False)
        if mail_read_set_read:
            return
        return super(mail_message,self).set_message_read( cr, uid, msg_ids, read, create_missing, context)
    
        
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


    def _notify_email(self, cr, uid, ids, message_id, force_send=False, user_signature=True, context=None):
        self.web_notification( cr, uid, ids, message_id, context=context)
        return super(mail_notification,self)._notify_email( cr, uid, ids, message_id, force_send, user_signature, context)
    
    
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:





