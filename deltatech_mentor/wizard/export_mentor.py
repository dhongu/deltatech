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



from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp

from openerp.addons.email_template import html2text
#import html2text

class export_mentor(models.TransientModel):
    _name = 'export.mentor'
    _description = "Export Mentor"


    name  = fields.Char(string='File Name', readonly=True) 
    data_file =  fields.Binary(string='File', readonly=True) 
    state = fields.Selection([('choose', 'choose'),   # choose period
                               ('get', 'get')],default='choose')        # get the file

   
    period_id = fields.Many2one('account.period', string='Period' , required=True )
    
    result = fields.Html(string="Result Export",readonly=True) 


    @api.multi
    def do_export(self):

        

   
        buff = StringIO.StringIO()
        
        files = []
         
        # This is my zip file
        zip_archive = zipfile.ZipFile(buff, mode='w')
        
        zip_archive.comment = 'Arhiva pentru Mentor'
        
        
            
        partner_ids = self.env['res.partner']     
        product_ids = self.env['product.template']
        invoice_in_ids = self.env['account.invoice'].search([('period_id','=',self.period_id.id),('type','in',['in_invoice','in_refund'])])
        
        for invoice in invoice_in_ids:
            for line in invoice.invoice_line:
                product_ids |= line.product_id.product_tmpl_id

        for invoice in invoice_in_ids:
            partner_ids |=  invoice.commercial_partner_id

        invoice_out_ids = self.env['account.invoice'].search([('period_id','=',self.period_id.id),('type','in',['out_invoice','out_refund'])])
        
        for invoice in invoice_out_ids:
            for line in invoice.invoice_line:
                product_ids |= line.product_id.product_tmpl_id

        for invoice in invoice_out_ids:
            partner_ids |=  invoice.commercial_partner_id 


        result_html = ' <div>Au fost exportate:</div>' 
        result_html += '<div>Facturi de intrare: %s</div>' % str(len(invoice_in_ids))
        result_html += '<div>Facturi de iesire %s</div>' % str(len(invoice_out_ids))
        result_html += '<div>Produse %s</div>' % str(len(product_ids))
        result_html += '<div>Parteneri %s</div>' % str(len(partner_ids))

        if  invoice_in_ids:         
            result = self.env['report'].get_html(records=invoice_in_ids, report_name='deltatech_mentor.report_invoice_in_template')
            result = html2text.html2text(result).encode('utf8')   
            result = result.replace(chr(13), '\n')
            result = result.replace('\n\n', '\r\n')
            zip_archive.writestr('Facturi_Intrare.txt', result)
            

        if  invoice_out_ids:         
            result = self.env['report'].get_html(records=invoice_out_ids, report_name='deltatech_mentor.report_invoice_in_template')
            result = html2text.html2text(result).encode('utf8')   
            result = result.replace(chr(13), '\n')
            result = result.replace('\n\n', '\r\n')
            zip_archive.writestr('Facturi_Iesire.txt', result)


        if product_ids:          
            result = self.env['report'].get_html(records=product_ids, report_name='deltatech_mentor.report_product_template')
            result = html2text.html2text(result).encode('utf8')   
            result = result.replace(chr(13), '\n')
            result = result.replace('\n\n', '\r\n')
            zip_archive.writestr('Articole.txt', result)            


        if  partner_ids:           
            result = self.env['report'].get_html(records=partner_ids, report_name='deltatech_mentor.report_res_partner')
            result = html2text.html2text(result).encode('utf8')   
            result = result.replace(chr(13), '\n')
            result = result.replace('\n\n', '\r\n')
            zip_archive.writestr('Partner.txt', result)
    
        # Here you finish editing your zip. Now all the information is
        # in your buff StringIO object
        zip_archive.close()
        
      
  
        out = base64.encodestring(buff.getvalue())
        buff.close()
        
        filename = 'ExportOdoo' + self.period_id.name
        extension = 'zip'
        
        
        name = "%s.%s" % (filename, extension)
        self.write({ 'state': 'get', 
                     'data_file': out, 
                     'name': name,
                     'result':result_html })
        
        
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'export.mentor',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
        



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
