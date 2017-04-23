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



from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp


try: 
    import html2text
except:
    from odoo.addons.email_template import html2text
    

class export_mentor(models.TransientModel):
    _name = 'export.mentor'
    _description = "Export Mentor"


    name  = fields.Char(string='File Name', readonly=True) 
    data_file =  fields.Binary(string='File', readonly=True) 
    state = fields.Selection([('choose', 'choose'),   # choose period
                               ('get', 'get')],default='choose')        # get the file

  
    item_details = fields.Boolean(string="Item Details")
    code_article = fields.Char(string="Code Article")

    period_id = fields.Many2one('account.period', string='Period' , required=True )
    
    result = fields.Html(string="Result Export",readonly=True) 

    journal_ids = fields.Many2many('account.journal', string='Journals')


    @api.multi
    def do_export(self):


        buff = StringIO.StringIO()
        
        files = []
         
        # This is my zip file
        zip_archive = zipfile.ZipFile(buff, mode='w')
        
        zip_archive.comment = 'Arhiva pentru Mentor'
        

        partner_ids = self.env['res.partner']     
        product_ids = self.env['product.template']
        
        domain = [('period_id','=',self.period_id.id),
                 ('state','in',['open','paid']),
                 ('type','in',['in_invoice','in_refund'])]
        if self.journal_ids:
            domain += [('journal_id','in',self.journal_ids.ids)]        
        invoice_in_ids = self.env['account.invoice'].search(domain)
        
        
        if self.item_details:
            for invoice in invoice_in_ids:
                for line in invoice.invoice_line_ids:
                    product_ids |= line.product_id.product_tmpl_id

        for invoice in invoice_in_ids:
            partner_ids |=  invoice.commercial_partner_id

        domain = [('period_id','=',self.period_id.id),
                  ('state','in',['open','paid']),
                  ('type','in',['out_invoice','out_refund'])]
        
        if self.journal_ids:
            domain += [('journal_id','in',self.journal_ids.ids)]
        
        invoice_out_ids = self.env['account.invoice'].search(domain)
        
        if self.item_details:
            for invoice in invoice_out_ids:
                for line in invoice.invoice_line_ids:
                    product_ids |= line.product_id.product_tmpl_id

        for invoice in invoice_out_ids:
            partner_ids |=  invoice.commercial_partner_id 


        result_html = ' <div>Au fost exportate:</div>' 
        result_html += '<div>Facturi de intrare: %s</div>' % str(len(invoice_in_ids))
        result_html += '<div>Facturi de iesire %s</div>' % str(len(invoice_out_ids))
        result_html += '<div>Produse %s</div>' % str(len(product_ids))
        result_html += '<div>Parteneri %s</div>' % str(len(partner_ids))

        data = {'item_details':self.item_details,
                'code_article':self.code_article}

        if  invoice_in_ids:         
            result = self.env['report'].get_html(records=invoice_in_ids, report_name='deltatech_mentor.report_invoice', data=data)
            if result:
                result = html2text.html2text(result).decode('utf8','replace')   
                result = result.replace(chr(13), '\n')
                result = result.replace('\n\n', '\r\n')
                zip_archive.writestr('Facturi_Intrare.txt', result.encode('utf8' ))
            

        if  invoice_out_ids:         
            result = self.env['report'].get_html(records=invoice_out_ids, report_name='deltatech_mentor.report_invoice', data=data)
            if result:
                result = html2text.html2text(result.decode('utf8','replace'))   
                result = result.replace(chr(13), '\n')
                result = result.replace('\n\n', '\r\n')
                zip_archive.writestr('Facturi_Iesire.txt', result.encode('utf8'))


        if product_ids:          
            result = self.env['report'].get_html(records=product_ids, report_name='deltatech_mentor.report_product_template')
            if result:
                result = html2text.html2text(result.decode('utf8','replace'))   
                result = result.replace(chr(13), '\n')
                result = result.replace('\n\n', '\r\n')
                zip_archive.writestr('Articole.txt', result.encode('utf8'))            

        
        if  partner_ids:           
            result = self.env['report'].get_html(records=partner_ids, report_name='deltatech_mentor.report_res_partner')
            if result:     
                result = html2text.html2text(result.decode('utf8','replace')) 
                result = result.replace(chr(13), '\n')
                result = result.replace('\n\n', '\r\n')
                zip_archive.writestr('Partner.txt', result.encode('utf8'))
        
        # Here you finish editing your zip. Now all the information is
        # in your buff StringIO object
        zip_archive.close()
        
      
  
        out = base64.encodestring(buff.getvalue())
        buff.close()
        
        filename = 'ExportOdooMentor' + self.period_id.name
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
