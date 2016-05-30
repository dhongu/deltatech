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


import socket

class fetchmail_server(models.Model):
    _inherit = 'fetchmail.server' 

    
    def fetch_mail(self, cr, uid, ids, context=None):
        # aici trebuie sa citesc care este serverui de pe care se ruleaza si daca este egal cu cel 
        hostname = socket.gethostname()
        dbname  = self.pool.db.dbname
        
        res = super(fetchmail_server,self).fetch_mail(cr, uid, ids, context)
        
        return res
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: