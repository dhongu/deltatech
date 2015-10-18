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

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp


try: 
    import html2text
except:
    from openerp.addons.email_template import html2text
    

class export_saga(models.TransientModel):
    _name = 'export.saga'
    _description = "Export Saga"


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


        date_start = fields.Date.from_string(self.period_id.date_start)
        date_stop = fields.Date.from_string(self.period_id.date_stop)

        """

        furnizori_file = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'data', 'Furnizori.dbf')
        furnizori_table = dbf.Table(furnizori_file)
        furnizori_table.delete_record()
        furnizori_table.pack()

        
        for partner in partner_ids:
            if partner.supplier:
                furnizori_table.COD = partner.id
                furnizori_table.DENUMIRE = partner.name
                furnizori_table.COD_FISCAL = partner.vat
                furnizori_table.write_record()
        """

        result_html = ' <div>Au fost exportate:</div>' 
        result_html += '<div>Facturi de intrare: %s</div>' % str(len(invoice_in_ids))
        result_html += '<div>Facturi de iesire %s</div>' % str(len(invoice_out_ids))
        result_html += '<div>Produse %s</div>' % str(len(product_ids))
        result_html += '<div>Parteneri %s</div>' % str(len(partner_ids))


        """
Furnizori 
Nr. crt. Nume câmp Tip Mărime câmp Descriere 

7. BANCA Character 48 Banca (optional) 
8. CONT_BANCA Character 36 Contul bancar (optional) 
9. FILIALA Character 36 Filiala Banca (optional) 
10. GRUPA Character 16 Grupa de furnizor (optional) 
11. AGENT Character 4 Cod agent (optional) 
12. DEN_AGENT Character 36 Nume agent (optional) 
13. TIP_TERT Character 1 I pt. intracomunitar, E pt. extracomunitari 
14. TARA Character 2 Codul de tara (RO) 
15. TEL Character 20 Numar telefon (optional) 
16. EMAIL Character 100 Email (optional) 
17. IS_TVA Numeric 1 1, dacă este platitor de TVA 
        """

        Furnizori = {
             'COD' :        dbf_fields.CharField(max_length=5),  #Cod furnizor 
             'DENUMIRE' :   dbf_fields.CharField(max_length=48), #Denumire furnizor 
             'COD_FISCAL':  dbf_fields.CharField(max_length=13), #Cod Fiscal, furnizor  
             'ANALITIC':    dbf_fields.CharField(max_length=16), #Cont analitic 
             'ZS':          dbf_fields.IntegerField(size=3),     #Numeric 3 Zile Scadenţă (optional) 
             'ADRESA':      dbf_fields.CharField(max_length=48),  #Adresa (optional) 
             }
        temp_file = StringIO.StringIO()
        furnizori_dbf = base.DBF(temp_file, Furnizori)
        for partner in partner_ids:
            if partner.supplier:
                cod_fiscal = partner.vat[2:] if partner.vat[:2]=='RO' else partner.vat
                values = {'COD':partner.id,
                          'DENUMIRE' :   partner.name[:48].encode('utf8' ),
                          'COD_FISCAL' : cod_fiscal,
                          'ANALITIC':    partner.property_account_payable.code,
                          'ZS':0,
                          'ADRESA':      partner.contact_address.encode('utf8' ),
                          }
                furnizori_dbf.insert(values)
                        


              
        file_name = 'Furnizori_'+date_start.strftime("%d-%m-%Y")+'_'+date_stop.strftime("%d-%m-%Y")+'.dbf'   
        zip_archive.writestr(file_name,temp_file.getvalue())
   
        """


7. DISCOUNT Numeric 5,2 Procent de discount acordat (optional) 
8. ADRESA Character 48 Adresa (optional) 
9. JUDET Character 36 Judeţ (optional) 
10. BANCA Character 36 Banca (optional) 
11. CONT_BANCA Character 36 Contul bancar (optional) 
12. DELEGAT Character 36 Numele şi prenumele delegatului (optional) 
13. BI_SERIE Character 2 Seria actului de identitate a delegatului (op.) 
14. BI_NUMAR Character 8 Număr act identitate, a delegatului (optional) 
15. BI_POL Character 16 Eliberat de... (optional) 
16. MASINA Character 16 Număr maşină delegat (optional) 
17. INF_SUPL Character 100 Informaltii care apar pe factura (optional) 
18. AGENT Character 4 Cod agent (optional) 
19. DEN_AGENT Character 36 Nume agent (optional) 
20. GRUPA Character 16 Grupa de client (optional) 
21. TIP_TERT Character 1 I pt. intracomunitar, E pt. extracomunitari 
22. TARA Character 2 Codul de tara (RO) 
23. TEL Character 20 Numar telefon (optional) 
24. EMAIL Character 100 Email (optional) 
25. IS_TVA Numeric 1 1, dacă este platitor de TVA 
        """
        Clienti = {
             'COD' :        dbf_fields.CharField(max_length=5),  #Cod  
             'DENUMIRE' :   dbf_fields.CharField(max_length=48), #Denumire  
             'COD_FISCAL':  dbf_fields.CharField(max_length=13), #Cod Fiscal,   
             'REG_COM':     dbf_fields.CharField(max_length=16), #Nr.înregistrare la Registrul Comerţului 
             'ANALITIC':    dbf_fields.CharField(max_length=16), #Cont analitic 
             'ZS':          dbf_fields.IntegerField(size=3),     #Numeric 3 Zile Scadenţă (optional) 
             'ADRESA':      dbf_fields.CharField(max_length=48),  #Adresa (optional) 
             }
        temp_file = StringIO.StringIO()
        clienti_dbf = base.DBF(temp_file, Clienti)
        for partner in partner_ids:
            if partner.customer:
                cod_fiscal = partner.vat[2:] if partner.vat[:2]=='RO' else partner.vat
                values = {'COD':         partner.id,
                          'DENUMIRE' :   partner.name[:48].encode('utf8' ),
                          'COD_FISCAL':  cod_fiscal,
                          'REG_COM':     partner.nrc,
                          'ANALITIC':    partner.property_account_receivable.code,
                          'ZS':          0,
                          'ADRESA':      partner.contact_address[:48].encode('utf8' ),
                          }
                clienti_dbf.insert(values)
                        
        
              
        file_name = 'Clienti_'+date_start.strftime("%d-%m-%Y")+'_'+date_stop.strftime("%d-%m-%Y")+'.dbf'   
        zip_archive.writestr(file_name,temp_file.getvalue())   
  
        """
Articole 
Nr. crt. Nume câmp Tip Mărime câmp Descriere 
1. COD Character 16 Cod articol 
2. DENUMIRE Character 60 Denumire articol 
3. UM Character 5 Unitate de masura 
4. TVA Numeric 5,2 Procent TVA articol 
5. TIP* Character 2 Cod tip 
6. DEN_TIP Character 36 Denumire tip 
7. PRET_VANZ Numeric 15,4 Pret de vanzare fara TVA (optional) 
8. PRET_V_TVA Numeric 15,4 Pret de vanzare cu TVA (optional) 
9. COD_BARE Character 16 Cod de bare (optional) 
10. CANT_MIN Numeric 14,3 Stoc minim (optional) 
11. GRUPA Character 16 Grupa de articol (optional) 
        """
        Articole = {
             'COD' :        dbf_fields.CharField(max_length=16),  #Cod  
             'DENUMIRE' :   dbf_fields.CharField(max_length=60), #Denumire 
             }
        temp_file = StringIO.StringIO()
        articole_dbf = base.DBF(temp_file, Articole)
        for product in product_ids:
            values = {'COD':product.id,
                      'DENUMIRE' :   product.name[:60],
                      }
            articole_dbf.insert(values)
                        
        file_name = 'Articole_'+date_start.strftime("%d-%m-%Y")+'_'+date_stop.strftime("%d-%m-%Y")+'.dbf'   
        zip_archive.writestr(file_name,temp_file.getvalue())         
        
        """
<Factura>
      <Antet>
            <FurnizorNume>   
            <FurnizorCIF>
            <FurnizorNrRegCom>
            <FurnizorCapital>
            <FurnizorAdresa>
            <FurnizorBanca>
            <FurnizorIBAN>
            <FurnizorInformatiiSuplimentare>
            <ClientNume>
            <ClientInformatiiSuplimentare>
            <ClientCIF>
            <ClientNrRegCom>
            <ClientAdresa>
            <ClientBanca>
            <ClientIBAN>
            <FacturaNumar>
            <FacturaData>
            <FacturaScadenta>
            <FacturaTaxareInversa> (Da/Nu)
            <FacturaTVAIncasare> (Da/Nu)
            <FacturaInformatiiSuplimentare>             <FacturaMoneda>
            <FacturaCotaTVA>
            <FacturaGreutate>
      </Antet>
      <Detalii>
            <Continut>
                  <Linie>
                        <LinieNrCrt>
                        <Gestiune>  (Optional)
                        <Descriere>
                        <CodArticolFurnizor>
                        <CodArticolClient>
                        <CodBare>
                        <InformatiiSuplimentare>
                        <UM>
                        <Cantitate>
                        <Pret>
                        <Valoare>
                        <TVA>
                  </Linie>
                  .......
                  <Linie>
                  .......
                  </Linie>
            </Continut>
      </Detalii>
      <Sumar>
            <TotalValoare>
            <TotalTVA>
            <Total>
      </Sumar>
      <Observatii>
            <txtObservatii>
            <SoldClient>
      </Observatii>
</Factura>
        
        """

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
            'res_model': 'export.saga',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
        



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
