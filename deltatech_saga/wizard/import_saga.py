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

import base64
import zipfile
import StringIO



from mydbf import base, fields as dbf_fields

import os

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
import unicodedata

try: 
    import html2text
except:
    from odoo.addons.email_template import html2text
    

class import_saga(models.TransientModel):
    _name = 'import.saga'
    _description = "Import Saga"

    state = fields.Selection([('choose', 'choose'),   # choose period
                               ('result', 'result')],default='choose')        # get the file

    supplier_file =  fields.Binary(string='Suppliers File') 
    customer_file =  fields.Binary(string='Customers File') 

    result = fields.Html(string="Result Export",readonly=True) 


    @api.multi
    def do_import(self):
        
        supplier_file = base64.decodestring(self.supplier_file)
        buff = StringIO.StringIO(supplier_file)
        db = base.DBF(usersfile)
        

        
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: