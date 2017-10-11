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

import StringIO
import base64
import unicodedata
import zipfile

from mydbf import base, fields as dbf_fields
from odoo import models, fields, api, _
from odoo.exceptions import Warning

try:
    import html2text
except:
    from odoo.addons.mail.models import html2text


class export_saga(models.TransientModel):
    _name = 'export.saga'
    _description = "Export Saga"

    name = fields.Char(string='File Name', readonly=True)
    data_file = fields.Binary(string='File', readonly=True)
    state = fields.Selection([('choose', 'choose'),  # choose period
                              ('get', 'get')], default='choose')  # get the file

    period_id = fields.Many2one('account.period', string='Period', required=True) # de inlocuit cu un interval
    ignore_error = fields.Boolean(string='Ignore Errors')
    export_product = fields.Boolean(string='Export Products', default=False, help="Pentru evidenta cantitativa")

    result = fields.Html(string="Result Export", readonly=True)

    def unaccent(self, text):
        """
        Strip accents from input String.
    
        :param text: The input string.
        :type text: String.
    
        :returns: The processed String.
        :rtype: String.
        """
        """
        try:
            text = unicode(text, 'utf-8')
        except NameError: # unicode is a default on python 3 
            pass
        """
        text = unicodedata.normalize('NFD', text)
        text = text.encode('ascii', 'ignore')
        text = text.decode("utf-8")
        text = text.replace(chr(13), ' ')
        text = text.replace('\n', ' ')
        return str(text)

    @api.model
    def do_export_furnizori(self, partner_ids):

        """
        Furnizori 
        Nr. crt. Nume câmp Tip Mărime câmp Descriere 
        
         
        8. CONT_BANCA Character 36 Contul bancar (optional) 
        9. FILIALA Character 36 Filiala Banca (optional) 
        10. GRUPA Character 16 Grupa de furnizor (optional) 
        11. AGENT Character 4 Cod agent (optional) 
        12. DEN_AGENT Character 36 Nume agent (optional) 
        13. TIP_TERT Character 1 I pt. intracomunitar, E pt. extracomunitari 



        """
        result_html = ''
        Furnizori = {
            'COD': dbf_fields.CharField(max_length=5),  # Cod furnizor
            'DENUMIRE': dbf_fields.CharField(max_length=48),  # Denumire furnizor
            'COD_FISCAL': dbf_fields.CharField(max_length=13),  # Cod Fiscal, furnizor
            'ANALITIC': dbf_fields.CharField(max_length=16),  # Cont analitic
            'ZS': dbf_fields.IntegerField(size=3),  # Numeric 3 Zile Scadenţă (optional)
            'ADRESA': dbf_fields.CharField(max_length=48),  # Adresa (optional)
            # 'BANCA':       dbf_fields.CharField(max_length=48),  #Banca (optional)
            'TARA': dbf_fields.CharField(max_length=2),  # Codul de tara (RO)
            'TEL': dbf_fields.CharField(max_length=20),  # Numar telefon (optional)
            'EMAIL': dbf_fields.CharField(max_length=100),  # Email (optional)
            'IS_TVA': dbf_fields.IntegerField(size=1),  # Numeric 1 1, dacă este platitor de TVA
        }
        temp_file = StringIO.StringIO()
        furnizori_dbf = base.DBF(temp_file, Furnizori)
        for partner in partner_ids:
            if not partner.ref_supplier:
                error = _("Partenerul %s nu are cod de furnizor SAGA") % partner.name
                result_html += '<div>Eroare %s</div>' % error
                if not self.ignore_error:
                    raise Warning(error)

            if not partner.vat_subjected:
                cod_fiscal = partner.vat[2:] if partner.vat and partner.vat[:2] == 'RO' else partner.vat
                is_tva = 0
            else:
                cod_fiscal = partner.vat
                is_tva = 1

            if partner.ref_supplier:
                analitic = '401.' + partner.ref_supplier.zfill(5)
            else:
                analitic = ''

            if partner.ref_supplier:
                partner_code = partner.ref_supplier.zfill(5)
            else:
                partner_code = ''

            values = {'COD': partner_code,
                      'DENUMIRE':  partner.name[:48],
                      'COD_FISCAL': cod_fiscal or '',
                      'ANALITIC': analitic,
                      'ZS': 0,
                      'ADRESA':  partner.contact_address,
                      # 'BANCA'
                      'TARA': partner.country_id.code or '',
                      'TEL': partner.phone or '',
                      'EMAIL': partner.email or '',
                      'IS_TVA': is_tva,
                      }
            for key in values:
                if isinstance(values[key], unicode):
                    values[key] = self.unaccent(values[key])
            furnizori_dbf.insert(values)

        return temp_file, result_html

    @api.model
    def do_export_clienti(self, partner_ids):

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
 
        """
        result_html = ''
        Clienti = {
            'COD': dbf_fields.CharField(max_length=5),  # Cod
            'DENUMIRE': dbf_fields.CharField(max_length=48),  # Denumire
            'COD_FISCAL': dbf_fields.CharField(max_length=13),  # Cod Fiscal,
            'REG_COM': dbf_fields.CharField(max_length=16),  # Nr.înregistrare la Registrul Comerţului
            'ANALITIC': dbf_fields.CharField(max_length=16),  # Cont analitic
            'ZS': dbf_fields.IntegerField(size=3),  # Numeric 3 Zile Scadenţă (optional)
            'ADRESA': dbf_fields.CharField(max_length=48),  # Adresa (optional)
            'TARA': dbf_fields.CharField(max_length=2),  # Codul de tara (RO)
            'TEL': dbf_fields.CharField(max_length=20),  # Numar telefon (optional)
            'EMAIL': dbf_fields.CharField(max_length=100),  # Email (optional)
            'IS_TVA': dbf_fields.IntegerField(size=1),  # Numeric 1 1, dacă este platitor de TVA
        }
        temp_file = StringIO.StringIO()
        clienti_dbf = base.DBF(temp_file, Clienti)
        for partner in partner_ids:

            if not partner.ref_customer:
                error = _("Partenerul %s nu are cod de client SAGA") % partner.name
                result_html += '<div>Eroare %s</div>' % error
                if not self.ignore_error:
                    raise Warning(error)

            if not partner.vat_subjected:
                cod_fiscal = partner.vat[2:] if partner.vat and partner.vat[:2] == 'RO' else partner.vat
                is_tva = 0
            else:
                cod_fiscal = partner.vat
                is_tva = 1

            if partner.ref_customer:
                analitic = '4111.' + partner.ref_customer.zfill(5)
            else:
                analitic = ''

            if partner.ref_customer:
                partner_code = partner.ref_customer.zfill(5)
            else:
                partner_code = ''

            values = {'COD': partner_code,
                      'DENUMIRE': partner.name[:48],
                      'COD_FISCAL': cod_fiscal or '',
                      'REG_COM': partner.nrc or '',
                      'ANALITIC': analitic,
                      'ZS': 0,
                      'ADRESA': partner.contact_address[:48],
                      'TARA': partner.country_id.code or '',
                      'TEL': partner.phone or '',
                      'EMAIL': partner.email or '',
                      'IS_TVA': is_tva,
                      }
            for key in values:
                if isinstance(values[key], unicode):
                    values[key] = self.unaccent(values[key])
            clienti_dbf.insert(values)

        return temp_file, result_html

    @api.model
    def do_export_articole(self, product_ids):

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
        result_html = ''
        Articole = {
            'COD': dbf_fields.CharField(max_length=16),  # Cod articol
            'DENUMIRE': dbf_fields.CharField(max_length=60),  # Denumire articol
            'UM': dbf_fields.CharField(max_length=5),  # Unitate de masura
            'TIP': dbf_fields.CharField(max_length=2),  # Cod tip
            'DEN_TIP': dbf_fields.CharField(max_length=36),  # Denumire tip
            'TVA': dbf_fields.DecimalField(size=5, deci=2),  # TVA
        }
        temp_file = StringIO.StringIO()
        articole_dbf = base.DBF(temp_file, Articole)
        for product in product_ids:
            if product.taxes_id:
                tva = int(product.taxes_id[0].amount * 100)
            else:
                tva = 0

            values = {
                'COD': product.default_code or '',
                'DENUMIRE': product.name[:60],
                'UM': product.uom_id.name[:5].split(' ')[0],

                'TIP': product.categ_id.code_saga or '',
                'DEN_TIP': product.categ_id.name[:36],
                'TVA': tva,
            }
            articole_dbf.insert(values)

        return temp_file, result_html

    @api.model
    def do_export_intrari(self, invoice_in_ids, voucher_in_ids):
        """
         Intrări
        Nr. crt. Nume câmp Tip Mărime câmp Descriere
        1. NR_NIR Numeric 7 Număr NIR
        2. NR_INTRARE Character 16 Numărul documentului de intrare
        3. GESTIUNE Character 4 Cod gestiune (optional)
        4. DEN_GEST Character 36 Denumirea gestiunii (optional)
        5. COD Character 5 Cod furnizor
        6. DATA Date - Data documentului de intrare (a facturii)
        7. SCADENT Date - Data scadenţei
        8. TIP Character 1 "A" - pentru aviz, "T" - taxare inversă...
        9. TVAI Numeric 1 1 pentru TVA la incasare
        10. COD_ART Character 16 Cod articol (optional)
        11. DEN_ART Character 60 Denumire articol
        12. UM Character 5 Unitatea de măsură pt.articol (optional)
        13. CANTITATE Numeric 14,3 Cantitate
        14. DEN_TIP Character 36 Denumirea tipului de articol (optional)
        15. TVA_ART Numeric 2 Procentul de TVA
        16. VALOARE Numeric 15,2 Valoarea totală, fără TVA
        17. TVA Numeric 15,2 TVA total
        18. CONT Character 20 Contul corespondent
        19. PRET_VANZ Numeric 15,2 Preţul de vânzare, (optional)
        20. GRUPA Character 16 Cod de grupa de articol contabil (optional)
        """
        result_html = ''


        Intrari = {
            'NR_NIR': dbf_fields.IntegerField(size=7),  # Număr NIR
            'NR_INTRARE': dbf_fields.CharField(max_length=16),  # Numărul documentului de intrare
            'GESTIUNE': dbf_fields.CharField(max_length=4),  # Cod gestiune (optional)
            'DEN_GEST': dbf_fields.CharField(max_length=36),  # Denumirea gestiunii (optional)
            'COD': dbf_fields.CharField(max_length=5),  # Cod furnizor
            'DATA': dbf_fields.DateField(),  # Data documentului de intrare (a facturii)
            'SCADENT': dbf_fields.DateField(),  # Data scadenţei
            'TIP': dbf_fields.CharField(max_length=1),  # "A" - pentru aviz, "T" - taxare inversă...
            'TVAI': dbf_fields.IntegerField(size=1),  # 1 pentru TVA la incasare
            'COD_ART': dbf_fields.CharField(max_length=16),  # Cod articol (optional)
            'DEN_ART': dbf_fields.CharField(max_length=60),  # Denumire articol
            'UM': dbf_fields.CharField(max_length=5),  # Unitatea de măsură pt.articol (optional)
            'CANTITATE': dbf_fields.DecimalField(size=14, deci=3),  # Cantitate
            'DEN_TIP': dbf_fields.CharField(max_length=36),  # Denumirea tipului de articol (optional)
            'TVA_ART': dbf_fields.IntegerField(size=2),  # Procentul de TVA
            'VALOARE': dbf_fields.DecimalField(size=15, deci=2),  # Valoarea totală, fără TVA
            'TVA': dbf_fields.DecimalField(size=15, deci=2),  # TVA total
            'CONT': dbf_fields.CharField(size=20),  # Contul corespondent
            'PRET_VANZ': dbf_fields.DecimalField(size=15, deci=2),  # TVA total
            'GRUPA': dbf_fields.CharField(max_length=16),  # Cod de grupa de articol contabil (optional)

        }

        temp_file = StringIO.StringIO()
        intrari_dbf = base.DBF(temp_file, Intrari)

        # todo: de convertit toate preturirile in RON

        for invoice in invoice_in_ids:

            tvai = 0
            """
            #todo: de scos din poxitia fiscala
            if invoice.vat_on_payment:
                tvai = 1
            """

            tip = ''
            """
            #todo: de unde mai e si asta?
            if invoice.fiscal_receipt:  # daca este un bon fiscal atunci
                tip = 'B'
            """

            for line in invoice.invoice_line_ids:
                if line.invoice_line_tax_id:
                    tva_art = int(line.invoice_line_tax_id[0].amount * 100)
                else:
                    tva_art = 0

                cont = line.account_id.code
                while cont[-1] == '0':
                    cont = cont[:-1]

                # inlocuire contrui de cheltuiala cu cele de stoc
                if cont == '6028':
                    cont = '3028'
                elif cont == '6022':
                    cont = '3022'
                elif cont == '623':
                    cont = '6231'

                if invoice.commercial_partner_id.ref_supplier:
                    partner_code = invoice.commercial_partner_id.ref_supplier.zfill(5)
                else:
                    partner_code = ''

                values = {
                    'NR_NIR': 10000 + int(''.join([s for s in invoice.number if s.isdigit()])),
                    'NR_INTRARE': invoice.supplier_invoice_number or invoice.number,
                    'GESTIUNE': '',
                    'DEN_GEST': '',
                    'COD': partner_code,
                    'DATA': fields.Date.from_string(invoice.date_invoice),
                    'SCADENT': fields.Date.from_string(invoice.date_due),
                    'TIP': tip,
                    'TVAI': tvai,

                    'DEN_ART': line.name[:60],
                    'UM': '',
                    'CANTITATE': line.quantity,

                    'TVA_ART': tva_art,
                    'VALOARE': line.price_subtotal,  # todo: daca pretul include tva valoarea cum o fi ?
                    'TVA': line.price_taxes,
                    'CONT': cont,
                    'PRET_VANZ': 0,
                    'GRUPA': '',
                }
                if line.uom_id:
                    values['UM'] = line.uom_id.name[:5].split(' ')[0]

                if not self.export_product:
                    values['COD_ART'] = ''
                    values['DEN_TIP'] = ''
                else:
                    values['COD_ART'] = line.product_id.default_code or '',
                    values['DEN_TIP'] =  line.product_id.categ_id.name[:36]

                for key in values:
                    if isinstance(values[key], unicode):
                        values[key] = self.unaccent(values[key])
                intrari_dbf.insert(values)

        for voucher in voucher_in_ids:

            if voucher.tax_ids:  # daca este un bon fiscal atunci
                tip = 'C'  # facura simplificata
            else:
                tip = 'B'  # Bon de casa

            if voucher.tax_id:
                tva_art = int(voucher.tax_ids[0].amount * 100)
            else:
                tva_art = 0

            for line in voucher.line_ids:

                cont = line.account_id.code
                while cont[-1] == '0':
                    cont = cont[:-1]

                # inlocuire contrui de cheltuiala cu cele de stoc
                if cont == '6028':
                    cont = '3028'
                elif cont == '6022':
                    cont = '3022'
                elif cont == '623':
                    cont = '6231'

                if tva_art == 0:
                    tva = 0
                else:
                    tva = line.amount - line.untax_amount

                if voucher.partner_id.commercial_partner_id.ref_supplier:
                    partner_code = voucher.partner_id.commercial_partner_id.ref_supplier.zfill(5)
                else:
                    partner_code = ''

                values = {
                    'NR_NIR': 10000 + int(''.join([s for s in voucher.number if s.isdigit()])),
                    'NR_INTRARE': voucher.reference or voucher.number,
                    'GESTIUNE': '',
                    'DEN_GEST': '',
                    'COD': partner_code,
                    'DATA': fields.Date.from_string(voucher.date),
                    'SCADENT': fields.Date.from_string(voucher.date),
                    'TIP': tip,
                    'TVAI': 0,

                    'DEN_ART': '',
                    'UM': '',
                    'CANTITATE': 1,
                    'TVA_ART': tva_art,
                    'VALOARE': line.untax_amount or line.amount,  # todo: daca pretul include tva valoarea cum o fi ?
                    'TVA': tva,
                    'CONT': cont,
                    'PRET_VANZ': 0,
                    'GRUPA': '',
                }
                if not self.export_product:
                    values['COD_ART'] = ''
                    values['DEN_TIP'] = ''
                else:
                    values['COD_ART'] = line.product_id.default_code or '',
                    values['DEN_TIP'] = line.product_id.categ_id.name[:36]

                for key in values:
                    if isinstance(values[key], unicode):
                        values[key] = self.unaccent(values[key])
                intrari_dbf.insert(values)

        return temp_file, result_html

    @api.model
    def do_export_iesiri(self, invoice_out_ids):
        result_html = ''
        """
Ieşiri 
Nr. crt. Nume câmp Tip Mărime câmp Descriere 
1. NR_IESIRE Character 16 Numărul documentului de ieşire, bon 
2. COD Character 5 Cod client 
3. DATA Date - Data documentului de ieşire 
4. SCADENT Date - Data scadenţei 
5. TIP Character 1 "A" - pentru aviz, "T" - taxare inversă... 
6. TVAI Numeric 1 1 pentru TVA la incasare 
7. GESTIUNE Character 4 Cod gestiune (optional) 
8. DEN_GEST Character 36 Denumirea gestiunii (optional) 
9. COD_ART Character 16 Cod articol 
10. DEN_ART Character 60 Denumire articol 
11. UM Character 5 Unitatea de măsură pt.articol 
12. CANTITATE Numeric 14,3 Cantitate 
13. DEN_TIP Character 36 Denumirea tipului de articol (optional) 
14. TVA_ART Numeric 2 Procentul de TVA 
15. VALOARE Numeric 15,2 Valoarea totală, fără TVA 
16. TVA Numeric 15,2 TVA total 
17. CONT Character 20 Contul corespondent 
18. PRET_VANZ Numeric 15,2 Preţul de vânzare 
19. GRUPA Character 16 Cod de grupa de articol contabil (optional) 



Numele fişierului trebuie să fie în formatul următor: IE_<data-inceput>_<data-sfarsit>.dbf.
Fişierul va conţine câte o înregistrare pentru fiecare articol din factură. 

    """
        Iesiri = {

            'NR_IESIRE': dbf_fields.CharField(max_length=16),  # Numărul documentului de ieşire, bon
            'COD': dbf_fields.CharField(max_length=5),  # Cod client
            'DATA': dbf_fields.DateField(),  # Data documentului de ieşire
            'SCADENT': dbf_fields.DateField(),  # Data scadenţei
            'TIP': dbf_fields.CharField(max_length=1),  # "A" - pentru aviz, "T" - taxare inversă...
            'TVAI': dbf_fields.IntegerField(size=1),  # 1 pentru TVA la incasare
            'GESTIUNE': dbf_fields.CharField(max_length=4),  # Cod gestiune (optional)
            'DEN_GEST': dbf_fields.CharField(max_length=36),  # Denumirea gestiunii (optional)
            'COD_ART': dbf_fields.CharField(max_length=16),  # Cod articol (optional)
            'DEN_ART': dbf_fields.CharField(max_length=60),  # Denumire articol
            'UM': dbf_fields.CharField(max_length=5),  # Unitatea de măsură pt.articol (optional)
            'CANTITATE': dbf_fields.DecimalField(size=14, deci=3),  # Cantitate
            'DEN_TIP': dbf_fields.CharField(max_length=36),  # Denumirea tipului de articol (optional)
            'TVA_ART': dbf_fields.IntegerField(size=2),  # Procentul de TVA
            'VALOARE': dbf_fields.DecimalField(size=15, deci=2),  # Valoarea totală, fără TVA
            'TVA': dbf_fields.DecimalField(size=15, deci=2),  # TVA total
            'CONT': dbf_fields.CharField(size=20),  # Contul corespondent
            'PRET_VANZ': dbf_fields.DecimalField(size=15, deci=2),  # TVA total
            'GRUPA': dbf_fields.CharField(max_length=16),  # Cod de grupa de articol contabil (optional)

        }

        temp_file = StringIO.StringIO()
        iesiri_dbf = base.DBF(temp_file, Iesiri)

        # todo: de convertit toate preturirile in RON

        for invoice in invoice_out_ids:
            tvai = 0
            """
            #todo: de scos din poxitia fiscala
            if invoice.vat_on_payment:
                tvai = 1

            """
            for line in invoice.invoice_line_ids:
                if line.invoice_line_tax_id:
                    tva_art = int(line.invoice_line_tax_id[0].amount * 100)
                else:
                    tva_art = 0

                cont = line.account_id.code
                while cont[-1] == '0':
                    cont = cont[:-1]

                if invoice.commercial_partner_id.ref_customer:
                    partner_code = invoice.commercial_partner_id.ref_customer.zfill(5)
                else:
                    partner_code = ''

                values = {

                    'NR_IESIRE': invoice.number.replace('/', ' '),
                    'COD': partner_code,
                    'DATA': fields.Date.from_string(invoice.date_invoice),
                    'SCADENT': fields.Date.from_string(invoice.date_due),
                    'TIP': '',
                    'TVAI': tvai,
                    'GESTIUNE': '',
                    'DEN_GEST': '',
                    'COD_ART': line.product_id.default_code or '',
                    'DEN_ART':  line.name[:60],
                    'UM': '',
                    'CANTITATE': line.quantity,
                    'DEN_TIP': '',
                    'TVA_ART': tva_art,
                    'VALOARE': line.price_subtotal,  # todo: daca pretul include tva valoarea cum o fi ?
                    'TVA': line.price_taxes,
                    'CONT': cont,
                    'PRET_VANZ': 0,
                    'GRUPA': '',
                }
                if line.uom_id:
                    values['UM'] = line.uom_id.name[:5].split(' ')[0]
                if line.product_id.categ_id:
                    values['DEN_TIP'] =  line.product_id.categ_id.name[:36]

                if not self.export_product:
                    values['COD_ART'] = ''
                    values['DEN_TIP'] = ''

                for key in values:
                    if isinstance(values[key], unicode):
                        values[key] = self.unaccent(values[key])
                iesiri_dbf.insert(values)
        return temp_file, result_html

    @api.multi
    def do_export(self):

        buff = StringIO.StringIO()

        files = []

        # This is my zip file
        zip_archive = zipfile.ZipFile(buff, mode='w')

        zip_archive.comment = 'Arhiva pentru Saga'

        partner_in_ids = self.env['res.partner']

        product_ids = self.env['product.template']

        invoice_in_ids = self.env['account.invoice'].search([('period_id', '=', False)])
        for invoice in invoice_in_ids:
            period = self.env["account.period"].find(invoice.date)[:1]
            if period:
                invoice.write({'period_id': period.id})

        invoice_in_ids = self.env['account.invoice'].search([('period_id', '=', self.period_id.id),
                                                             ('state', 'in', ['open', 'paid']),
                                                             ('type', 'in', ['in_invoice', 'in_refund'])])

        voucher_in_ids = self.env['account.voucher'].search([('period_id', '=', self.period_id.id),
                                                             ('state', 'in', ['posted']),
                                                             ('voucher_type', 'in', ['purchase'])])

        if self.export_product:
            for invoice in invoice_in_ids:
                for line in invoice.invoice_line_ids:
                    product_ids |= line.product_id.product_tmpl_id

        for invoice in invoice_in_ids:
            partner_in_ids |= invoice.commercial_partner_id

        for voucher in voucher_in_ids:
            partner_in_ids |= voucher.partner_id.commercial_partner_id

        partner_out_ids = self.env['res.partner']
        invoice_out_ids = self.env['account.invoice'].search([('period_id', '=', self.period_id.id),
                                                              ('state', 'in', ['open', 'paid']),
                                                              ('type', 'in', ['out_invoice', 'out_refund'])])

        if self.export_product:
            for invoice in invoice_out_ids:
                for line in invoice.invoice_line_ids:
                    product_ids |= line.product_id.product_tmpl_id

        for invoice in invoice_out_ids:
            partner_out_ids |= invoice.commercial_partner_id

        date_start = fields.Date.from_string(self.period_id.date_start)
        date_stop = fields.Date.from_string(self.period_id.date_stop)

        result_html = ' <div>Au fost exportate:</div>'
        result_html += '<div>Facturi de intrare: %s</div>' % str(len(invoice_in_ids))
        result_html += '<div>Bonuri fiscale: %s</div>' % str(len(voucher_in_ids))
        result_html += '<div>Facturi de iesire %s</div>' % str(len(invoice_out_ids))
        result_html += '<div>Produse %s</div>' % str(len(product_ids))
        result_html += '<div>Furnizori %s</div>' % str(len(partner_in_ids))
        result_html += '<div>Client %s</div>' % str(len(partner_out_ids))

        temp_file, messaje = self.do_export_furnizori(partner_in_ids)

        result_html += messaje

        file_name = 'Furnizori_' + date_start.strftime("%d-%m-%Y") + '_' + date_stop.strftime("%d-%m-%Y") + '.dbf'
        zip_archive.writestr(file_name, temp_file.getvalue())

        temp_file, messaje = self.do_export_clienti(partner_out_ids)

        result_html += messaje

        file_name = 'Clienti_' + date_start.strftime("%d-%m-%Y") + '_' + date_stop.strftime("%d-%m-%Y") + '.dbf'
        zip_archive.writestr(file_name, temp_file.getvalue())

        if self.export_product:
            temp_file, messaje = self.do_export_articole(product_ids)

            result_html += messaje

            file_name = 'Articole_' + date_start.strftime("%d-%m-%Y") + '_' + date_stop.strftime("%d-%m-%Y") + '.dbf'
            zip_archive.writestr(file_name, temp_file.getvalue())

        temp_file, messaje = self.do_export_intrari(invoice_in_ids, voucher_in_ids)

        result_html += messaje

        file_name = 'IN_' + date_start.strftime("%d-%m-%Y") + '_' + date_stop.strftime("%d-%m-%Y") + '.dbf'
        zip_archive.writestr(file_name, temp_file.getvalue())

        temp_file, messaje = self.do_export_iesiri(invoice_out_ids)

        result_html += messaje

        file_name = 'IE_' + date_start.strftime("%d-%m-%Y") + '_' + date_stop.strftime("%d-%m-%Y") + '.dbf'
        zip_archive.writestr(file_name, temp_file.getvalue())

        zip_archive.close()
        out = base64.encodestring(buff.getvalue())
        buff.close()

        filename = 'ExportOdoo' + self.period_id.name
        extension = 'zip'

        name = "%s.%s" % (filename, extension)
        self.write({'state': 'get',
                    'data_file': out,
                    'name': name,
                    'result': result_html})

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
