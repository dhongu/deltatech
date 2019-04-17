# -*- coding: utf-8 -*-
# ©  2017 Deltatech
# See README.rst file on addons root folder for license details

import sys

PY2 = sys.version_info[0] == 2

if not PY2:
    unicode = str

from io import BytesIO

import base64
import unicodedata
import zipfile

from .mydbf import base, fields as dbf_fields
from odoo import models, fields, api, _
from odoo.exceptions import UserError
import datetime
from dateutil.relativedelta import relativedelta

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

    # period_id = fields.Many2one('account.period', string='Period', required=True) # de inlocuit cu un interval
    date_range_id = fields.Many2one('date.range', string='Date range')
    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today)
    ignore_error = fields.Boolean(string='Ignore Errors')
    export_product = fields.Boolean(string='Export Products', default=False, help="Pentru evidenta cantitativa")

    journal_ids = fields.Many2many('account.journal', strings='Journals')
    use_analitic = fields.Boolean(string="Foloseste conturi analitice la client si furnizori", default=True)
    result = fields.Html(string="Result Export", readonly=True)

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.model
    def default_get(self, fields_list):
        res = super(export_saga, self).default_get(fields_list)
        today = fields.Date.context_today(self)
        today = fields.Date.from_string(today)

        from_date = (today + relativedelta(day=1, months=-1, days=0))
        to_date = (today + relativedelta(day=1, months=0, days=-1))

        res['date_from'] = fields.Date.to_string(from_date)
        res['date_to'] = fields.Date.to_string(to_date)
        return res

    def unaccent(self, text):
        """
        Strip accents from input String.
    
        :param text: The input string.
        :type text: String.
    
        :returns: The processed String.
        :rtype: String.
        """

        text = unicodedata.normalize('NFD', text)
        text = text.encode('ascii', 'ignore')
        text = text.decode("utf-8")
        text = text.replace(chr(13), ' ')
        text = text.replace('\n', ' ')
        return str(text)

    def get_cont(self, account_id):
        if not account_id:
            return ''

        cont = account_id.code[:4]
        while cont[-1] == '0':
            cont = cont[:-1]
        analitic = int(account_id.code[4:])
        if analitic:
            cont += '.' + str(analitic)
        return cont

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
        temp_file = BytesIO()
        furnizori_dbf = base.DBF(temp_file, Furnizori)
        for partner in partner_ids:
            if not partner.ref_supplier:
                error = _("Partenerul %s nu are cod de furnizor SAGA") % partner.name
                result_html += '<div>Eroare %s</div>' % error
                if not self.ignore_error:
                    raise UserError(error)

            if partner.is_company:
                if not partner.vat:
                    error = _("Partenerul %s nu are CUI") % partner.name
                    result_html += '<div>Eroare %s</div>' % error
                    if not self.ignore_error:
                        raise UserError(error)

                if not partner.vat_subjected:
                    cod_fiscal = partner.vat[2:] if partner.vat and partner.vat[:2] == 'RO' else partner.vat
                    is_tva = 0
                else:
                    cod_fiscal = partner.vat
                    is_tva = 1
            else:
                is_tva = 0
                cod_fiscal = partner.cnp or partner.nrc

            if partner.ref_supplier:

                if self.use_analitic:
                    analitic = '401.' + partner.ref_supplier.zfill(5)
                else:
                    analitic = '401'
            else:
                analitic = ''

            if partner.ref_supplier:
                partner_code = partner.ref_supplier.zfill(5)
            else:
                partner_code = ''

            values = {'COD': partner_code,
                      'DENUMIRE': partner.name[:48],
                      'COD_FISCAL': cod_fiscal or '',
                      'ANALITIC': analitic,
                      'ZS': 0,
                      'ADRESA': partner.contact_address,
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
            'JUDET': dbf_fields.CharField(max_length=36),  # Judeţ (optional)
            'TARA': dbf_fields.CharField(max_length=2),  # Codul de tara (RO)
            'TEL': dbf_fields.CharField(max_length=20),  # Numar telefon (optional)
            'EMAIL': dbf_fields.CharField(max_length=100),  # Email (optional)
            'IS_TVA': dbf_fields.IntegerField(size=1),  # Numeric 1 1, dacă este platitor de TVA
            'TIP_TERT': dbf_fields.CharField(max_length=1),  # I pt. intracomunitar, E pt. extracomunitari
            'BANCA': dbf_fields.CharField(max_length=36),
            'CONT_BANCA': dbf_fields.CharField(max_length=36),
            'INF_SUPL': dbf_fields.CharField(max_length=100),  # Informaltii care apar pe factura (optional)
        }
        temp_file = BytesIO()
        clienti_dbf = base.DBF(temp_file, Clienti)
        for partner in partner_ids:

            if not partner.ref_customer:
                error = _("Partenerul %s nu are cod de client SAGA") % partner.name
                result_html += '<div>Eroare %s</div>' % error
                if not self.ignore_error:
                    raise UserError(error)

            if partner.is_company:
                if not partner.vat:
                    error = _("Partenerul %s nu are CUI") % partner.name
                    result_html += '<div>Eroare %s</div>' % error
                    if not self.ignore_error:
                        raise UserError(error)
                if not partner.vat_subjected:
                    cod_fiscal = partner.vat[2:] if partner.vat and partner.vat[:2] == 'RO' else partner.vat
                    is_tva = 0
                else:
                    cod_fiscal = partner.vat
                    is_tva = 1
            else:
                is_tva = 0
                cod_fiscal = partner.cnp or partner.nrc

            if partner.ref_customer:
                if self.use_analitic:
                    analitic = '4111.' + partner.ref_customer.zfill(5)
                else:
                    analitic = '4111'
            else:
                analitic = ''

            if partner.ref_customer:
                partner_code = partner.ref_customer.zfill(5)
            else:
                partner_code = ''

            if not partner.country_id:
                tip_tert = 'I'
            else:
                if partner.country_id.code == 'RO':
                    tip_tert = 'I'
                else:
                    tip_tert = 'E'
            values = {
                'COD': partner_code,
                'DENUMIRE': partner.name[:48],
                'COD_FISCAL': cod_fiscal or '',
                'REG_COM': partner.nrc or '',
                'ANALITIC': analitic,
                'ZS': 0,
                'ADRESA': partner.contact_address[:48],
                'JUDET': '',
                'TARA': partner.country_id.code or '',
                'TEL': partner.phone or '',
                'EMAIL': partner.email or '',
                'IS_TVA': is_tva,
                'TIP_TERT': tip_tert,
                'BANCA': '',
                'CONT_BANCA': '',
                'INF_SUPL': ''
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
            'PRET_VANZ': dbf_fields.DecimalField(size=15, deci=3),  # Pret de vanzare fara TVA
            'COD_BARE': dbf_fields.CharField(max_length=16)
        }
        temp_file = BytesIO()
        articole_dbf = base.DBF(temp_file, Articole)
        for product in product_ids:
            if product.taxes_id:
                tva = round(product.taxes_id[0].amount, 2)
            else:
                tva = 0

            if not product.categ_id.code_saga:
                error = _("Categoria %s a produsului  %s nu are cod SAGA") % (product.categ_id.name, product.name)
                result_html += '<div>Eroare %s</div>' % error
                if not self.ignore_error:
                    raise UserError(error)

            values = {
                'COD': product.default_code or '',
                'DENUMIRE': product.name[:60],
                'UM': product.uom_id.name[:5].split(' ')[0],

                'TIP': product.categ_id.code_saga or '',
                'DEN_TIP': product.categ_id.name[:36],
                'TVA': tva,
                'PRET_VANZ': product.list_price,
                'COD_BARE': ''
            }
            for key in values:
                if isinstance(values[key], unicode):
                    values[key] = self.unaccent(values[key])
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

        temp_file = BytesIO()
        intrari_dbf = base.DBF(temp_file, Intrari)

        # inlocuire contrui de cheltuiala cu cele de stoc
        # todo: de pus contruile acestea intr-o tabela de mapare sau intr-un parametru
        cont_mapping = {
            '6028': '3028',
            '6022': '3022',
            '623': '6231'
        }



        # todo: de convertit toate preturile in RON

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
                if line.invoice_line_tax_ids:
                    tva_art = int(line.invoice_line_tax_ids[0].amount)
                else:
                    tva_art = 0

                cont = self.get_cont(line.account_id.code)



                if cont in cont_mapping:
                    cont = cont_mapping[cont]

                if invoice.commercial_partner_id.ref_supplier:
                    partner_code = invoice.commercial_partner_id.ref_supplier.zfill(5)
                else:
                    partner_code = ''

                nr_int = ''.join([s for s in invoice.number if s.isdigit()])

                nr_int = 10000 + int(nr_int[-4:])
                nr_intrare = invoice.reference or invoice.number

                # price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                # currency = line.invoice_id and line.invoice_id.currency_id or None
                # taxes = False
                # if line.invoice_line_tax_ids:
                #     taxes = line.invoice_line_tax_ids.compute_all(price, currency, line.quantity,
                #                                                   product=line.product_id,
                #                                                   partner=line.invoice_id.partner_id)
                #     valoare_fara_tva =  taxes['total_excluded']
                #     valoare_cu_tva = taxes['total_included']
                #     valoare_tva = valoare_cu_tva - valoare_fara_tva
                # else:
                #     valoare_fara_tva = line.price_subtotal
                #     valoare_tva = 0
                values = {
                    'NR_NIR': nr_int,
                    'NR_INTRARE': nr_intrare[-16:],
                    'GESTIUNE': '',
                    'DEN_GEST': '',
                    'COD': partner_code,
                    'DATA': fields.Date.from_string(invoice.date_invoice),
                    'SCADENT': fields.Date.from_string(invoice.date_due),
                    'TIP': tip,
                    'TVAI': tvai,
                    'COD_ART': '',
                    'DEN_ART': line.name[:60],
                    'UM': '',
                    'CANTITATE': round(line.quantity, 3),
                    'DEN_TIP': '',
                    'TVA_ART': tva_art,
                    'VALOARE': round(line.price_subtotal, 2),  # todo: daca pretul include tva valoarea cum o fi ?
                    'TVA': round(line.price_total - line.price_subtotal, 2),
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
                    values['COD_ART'] = line.product_id.default_code and line.product_id.default_code[:16] or ''
                    if line.product_id.categ_id.name:
                        values['DEN_TIP'] = self.unaccent(line.product_id.categ_id.name[:36])
                    else:
                        values['DEN_TIP'] = ''

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
                tva_art = int(voucher.tax_ids[0].amount)
            else:
                tva_art = 0

            for line in voucher.line_ids:

                cont = self.get_cont(line.account_id.code)

                if cont in cont_mapping:
                    cont = cont_mapping[cont]


                if tva_art == 0:
                    tva = 0
                else:
                    tva = line.amount - line.untax_amount

                if voucher.partner_id.commercial_partner_id.ref_supplier:
                    partner_code = voucher.partner_id.commercial_partner_id.ref_supplier.zfill(5)
                else:
                    partner_code = ''

                nr_int = ''.join([s for s in invoice.number if s.isdigit()])

                nr_int = 10000 + int(nr_int[-4:])
                nr_intrare = voucher.reference or voucher.number
                valoare = line.untax_amount or line.amount

                values = {
                    'NR_NIR': nr_int,
                    'NR_INTRARE': nr_intrare[-16:],
                    'GESTIUNE': '',
                    'DEN_GEST': '',
                    'COD': partner_code,
                    'DATA': fields.Date.from_string(voucher.date),
                    'SCADENT': fields.Date.from_string(voucher.date),
                    'TIP': tip,
                    'TVAI': 0,
                    'COD_ART': '',
                    'DEN_ART': '',
                    'UM': '',
                    'CANTITATE': 1,
                    'TVA_ART': tva_art,
                    'VALOARE': round(valoare, 2),  # todo: daca pretul include tva valoarea cum o fi ?
                    'TVA': round(tva, 2),
                    'CONT': cont,
                    'PRET_VANZ': 0,
                    'GRUPA': '',
                }

                for key in values:
                    if isinstance(values[key], unicode):
                        values[key] = self.unaccent(values[key])
                intrari_dbf.insert(values)

        return temp_file, result_html

    @api.model
    def do_export_iesiri(self, invoice_out_ids):
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
        result_html = ''
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

        temp_file = BytesIO()
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
                if line.invoice_line_tax_ids:
                    tva_art = int(line.invoice_line_tax_ids[0].amount)
                else:
                    tva_art = 0

                cont = self.get_cont(line.account_id.code)



                if invoice.commercial_partner_id.ref_customer:
                    partner_code = invoice.commercial_partner_id.ref_customer.zfill(5)
                else:
                    partner_code = ''

                nr_out = ''.join([s for s in invoice.number if s.isdigit()])
                nr_out = int(nr_out[-16:])
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                currency = line.invoice_id and line.invoice_id.currency_id or None
                # taxes = False
                # if line.invoice_line_tax_ids:
                #     taxes = line.invoice_line_tax_ids.compute_all(price, currency, line.quantity,
                #                                                   product=line.product_id,
                #                                                   partner=line.invoice_id.partner_id)
                #     valoare_fara_tva = taxes['total_excluded']
                #     valoare_cu_tva = taxes['total_included']
                #     valoare_tva = valoare_cu_tva - valoare_fara_tva
                # else:
                #     valoare_fara_tva = line.price_subtotal
                #     valoare_tva = 0
                values = {

                    'NR_IESIRE': nr_out,
                    'COD': partner_code,
                    'DATA': fields.Date.from_string(invoice.date_invoice),
                    'SCADENT': fields.Date.from_string(invoice.date_due),
                    'TIP': '',
                    'TVAI': tvai,
                    'GESTIUNE': '',
                    'DEN_GEST': '',
                    'COD_ART': line.product_id.default_code and line.product_id.default_code[:16] or '',
                    'DEN_ART': line.name[:60],
                    'UM': '',
                    'CANTITATE': round(line.quantity, 3),
                    'DEN_TIP': '',
                    'TVA_ART': tva_art,
                    'VALOARE': round(line.price_subtotal, 2),  # todo: daca pretul include tva valoarea cum o fi ?
                    'TVA': round(line.price_total - line.price_subtotal, 2),
                    'CONT': cont,
                    'PRET_VANZ': 0,
                    'GRUPA': '',
                }
                if line.uom_id:
                    values['UM'] = line.uom_id.name[:5].split(' ')[0]
                if line.product_id.categ_id:
                    values['DEN_TIP'] = line.product_id.categ_id.name[:36]

                if not self.export_product:
                    values['COD_ART'] = ''
                    values['DEN_TIP'] = ''

                for key in values:
                    if isinstance(values[key], unicode):
                        values[key] = self.unaccent(values[key])
                iesiri_dbf.insert(values)
        return temp_file, result_html

    @api.model
    def do_export_nc(self, account_moves):
        """
        Articole contabile
        Nr. crt. Nume câmp Tip Mărime câmp Descriere
        1. NDP Character 10 Număr articol contabil
        2. CONT_D Character 20 Contul debitor
        3. CONT_C Character 20 Contul creditor
        4. SUMA Numeric 15,2 Suma înregistrată cu articolul contabil
        5. CURS Numeric 15,4 Curs valutar  (optional)
        6. SUMA_VAL Numeric 14,2 Suma în valută  (optional)
        7. DATA Date - Data articolului contabil
        8. EXPLICATIE Character 48 Explicaţie, articol contabil
        9. GRUPA Character 16 Grupa asociată (optional)


        Numele fişierului trebuie să fie în formatul următor: NC_<data-inceput>_<data-sfarsit>.dbf

        """
        result_html = ''
        Note = {
            'NDP': dbf_fields.CharField(max_length=10),  # Număr articol contabil
            'CONT_D': dbf_fields.CharField(max_length=20),  # Contul debitor
            'CONT_C': dbf_fields.CharField(max_length=20),  # Contul creditor
            'SUMA': dbf_fields.DecimalField(size=15, deci=2),  # Suma înregistrată cu articolul contabil
            'CURS': dbf_fields.DecimalField(size=15, deci=2),  # Curs valutar  (optional)
            'SUMA_VAL': dbf_fields.DecimalField(size=15, deci=2),  # Numeric 14,2 Suma în valută  (optional)
            'DATA': dbf_fields.DateField(),  # Data articolului contabil
            'EXPLICATIE': dbf_fields.CharField(max_length=48),  # Explicaţie, articol contabil
            'GRUPA': dbf_fields.CharField(max_length=16),  # Grupa asociată (optional)
        }

        temp_file = BytesIO()
        note_dbf = base.DBF(temp_file, Note)
        for account_move in account_moves:

            cont_d = ''
            cont_c = ''
            nr = 0
            for line in account_move.line_ids:
                cont = self.get_cont(line.account_id.code)

                if self.use_analitic:
                    if cont == '401' and line.partner_id.ref_supplier:
                        cont = '401.' + line.partner_id.ref_supplier.zfill(5)
                    if cont == '4111' and line.partner_id.ref_customer:
                        cont = '4111.' + line.partner_id.ref_customer.zfill(5)

                if cont == '531.1':  # din numerar in casa in lei
                    cont = '5311'
                if cont == '512.1':  # din banca in banca in lei
                    cont = '5121'

                suma = 0.0
                if line.credit != 0:
                    cont_c = cont
                    suma = line.credit

                if line.debit != 0:
                    cont_d = cont
                    suma = line.debit

                nr += 1
                if nr == 1:
                    if len(account_move.line_ids) == 2:
                        continue
                    else:
                        if line.credit == 0:
                            cont_c = '%'
                        else:
                            cont_d = '%'
                else:
                    if len(account_move.line_ids) != 2:
                        if line.credit == 0:
                            cont_c = ''
                        else:
                            cont_d = ''
                ndp = ''.join([s for s in account_move.name if s.isdigit()])

                if cont_d == '371' and cont_c == '4428.2':
                    cont_c = '4428.M'

                if cont_d == '4428.1' and cont_c == '371':
                    cont_d = '4428.M'

                if cont_c == '4428.1':
                    cont_c = '4428.TP'

                if cont_c == '4428.2':
                    cont_c = '4428.TI'

                if cont_d == '4428.1':
                    cont_d = '4428.TP'

                if cont_d == '4428.2':
                    cont_d = '4428.TI'

                values = {
                    'NDP': ndp[-10:],
                    'CONT_D': cont_d,
                    'CONT_C': cont_c,
                    'SUMA': suma,
                    'CURS': 0.0,
                    'SUMA_VAL': 0.0,
                    'DATA': fields.Date.from_string(account_move.date),
                    'EXPLICATIE': line.name,
                    'GRUPA': '',
                }

                for key in values:
                    if isinstance(values[key], unicode):
                        values[key] = self.unaccent(values[key])
                note_dbf.insert(values)
        return temp_file, result_html

    @api.multi
    def do_export(self):

        buff = BytesIO()

        files = []

        # This is my zip file
        zip_archive = zipfile.ZipFile(buff, mode='w')

        # zip_archive.comment = 'Arhiva pentru Saga'

        partner_in_ids = self.env['res.partner']

        product_ids = self.env['product.template']

        account_move_line_ids = self.env['account.move.line']
        account_move_ids = self.env['account.move']

        '''
        invoice_in_ids = self.env['account.invoice'].search([('period_id', '=', False)])
        for invoice in invoice_in_ids:
            period = self.env["account.period"].find(invoice.date)[:1]
            if period:
                invoice.write({'period_id': period.id})
        '''

        if self.journal_ids:
            account_move_ids = self.env['account.move'].search([('date', '>=', self.date_from),
                                                                ('date', '<=', self.date_to),
                                                                ('state', '=', 'posted'),
                                                                ('journal_id', 'in', self.journal_ids.ids)])

        invoice_in_ids = self.env['account.invoice'].search([('date', '>=', self.date_from),
                                                             ('date', '<=', self.date_to),
                                                             ('state', 'in', ['open', 'paid']),
                                                             ('type', 'in', ['in_invoice', 'in_refund'])])

        voucher_in_ids = self.env['account.voucher'].search([('date', '>=', self.date_from),
                                                             ('date', '<=', self.date_to),
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
        invoice_out_ids = self.env['account.invoice'].search([('date', '>=', self.date_from),
                                                              ('date', '<=', self.date_to),
                                                              ('state', 'in', ['open', 'paid']),
                                                              ('type', 'in', ['out_invoice', 'out_refund'])])

        if self.export_product:
            for invoice in invoice_out_ids:
                for line in invoice.invoice_line_ids:
                    product_ids |= line.product_id.product_tmpl_id

        for invoice in invoice_out_ids:
            partner_out_ids |= invoice.commercial_partner_id

        for account_move in account_move_ids:
            account_move_line_ids |= account_move.line_ids

        for line in account_move_line_ids:
            if line.partner_id and line.partner_id.customer:
                partner_out_ids |= line.partner_id
            if line.partner_id and line.partner_id.supplier:
                partner_in_ids |= line.partner_id

        date_start = fields.Date.from_string(self.date_from)
        date_stop = fields.Date.from_string(self.date_to)

        result_html = ' <div>Au fost exportate:</div>'
        result_html += '<div>Facturi de intrare: %s</div>' % str(len(invoice_in_ids))
        result_html += '<div>Bonuri fiscale: %s</div>' % str(len(voucher_in_ids))
        result_html += '<div>Facturi de iesire %s</div>' % str(len(invoice_out_ids))
        result_html += '<div>Note contabile %s</div>' % str(len(account_move_ids))
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

        if account_move_line_ids:
            temp_file, messaje = self.do_export_nc(account_move_ids)
            result_html += messaje
            file_name = 'NC_' + date_start.strftime("%d-%m-%Y") + '_' + date_stop.strftime("%d-%m-%Y") + '.dbf'
            zip_archive.writestr(file_name, temp_file.getvalue())

        zip_archive.close()
        out = base64.b64encode(buff.getvalue())
        buff.close()

        filename = 'ExportOdoo_%s_%s' % (self.date_from, self.date_to)
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
