# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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
from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp


try: 
    import html2text
except:
    from openerp.addons.email_template import html2text
    

class export_datecs(models.TransientModel):
    _name = 'export.datecs'
    _description = "Export Datecs"


    name  = fields.Char(string='File Name', readonly=True) 
    data_file =  fields.Binary(string='File', readonly=True) 
    invoice_id = fields.Many2one('account.invoice')
   
    
    @api.model
    def default_get(self, fields): 
        defaults = super(export_datecs, self).default_get(fields) 
        
        invoice_id = defaults.get('invoice_id', self.env.context.get('active_id', False))        
        
        if invoice_id:
            invoice = self.env['account.invoice'].browse(invoice_id)
            defaults['invoice_id'] = invoice.id

        
        if not invoice_id or invoice.type != 'out_invoice':
             raise Warning(_('Please select Customer Invoice %s') % invoice_id)
            

        out = False
        result = self.env['report'].get_html(records=invoice, report_name='deltatech_datecs_print.report_invoice')
        if result:
            result = html2text.html2text(result)  #.decode('utf8','replace')   
            result = result.replace(chr(13), '\n')
            result = result.replace('\n\n', '\r\n')
            out = base64.encodestring(result)
                
        
        filename = 'BF_'+invoice.number
        filename = "".join(i for i in filename if i not in "\/:*?<>|")
        
        extension = 'inp'
        
        
        defaults['name'] = "%s.%s" % (filename, extension)
        defaults['data_file'] =  out

    
        return defaults  
        



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
