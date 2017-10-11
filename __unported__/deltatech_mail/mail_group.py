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
 



class mail_group(models.Model):
    _inherit = 'mail.group' 
    

    @api.cr_uid_ids_context
    def message_post(self, cr, uid, thread_id, body='', subject=None, type='notification',
                     subtype=None, parent_id=False, attachments=None, context=None,
                     content_subtype='html', **kwargs):
        
        if context is None:
            context = {}  
         
        context = context.copy() 
        if 'mail_notify_noemail' not in context:
            context['mail_notify_noemail'] = False
        
        res = super(mail_group,self).message_post(  cr, uid, thread_id, body, subject, type,
                     subtype, parent_id, attachments, context, content_subtype, **kwargs)
        
        return res
           
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: