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
        


    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:





