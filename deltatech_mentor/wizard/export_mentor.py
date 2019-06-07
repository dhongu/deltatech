# -*- coding: utf-8 -*-
# ©  2017 Deltatech
# See README.rst file on addons root folder for license details


import base64
import zipfile
from io import StringIO
from io import BytesIO
import configparser

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp

import html2text
import odoo.addons.decimal_precision as dp


class export_mentor(models.TransientModel):
    _name = 'export.mentor'
    _description = "Export Mentor"

    name = fields.Char(string='File Name', readonly=True)
    data_file = fields.Binary(string='File', readonly=True)
    state = fields.Selection([('choose', 'choose'),  # choose period
                              ('get', 'get')], default='choose')  # get the file

    format_data = fields.Char('Format Data', default='%d.%m.%Y')
    without_discount = fields.Boolean('Without discout', default=True)

    item_details = fields.Boolean(string="Item Details")
    code_article = fields.Char(string="Code Article")

    date_range_id = fields.Many2one('date.range', string='Date range')
    date_from = fields.Date(string='Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date(string='End Date', required=True, default=fields.Date.today)

    result = fields.Html(string="Result Export", readonly=True)

    journal_ids = fields.Many2many('account.journal', string='Journals')

    location_id = fields.Many2one('stock.location', string='Stock location',
                                  domain=[('usage', '=', 'internal')], required=True, )

    prod_location_id = fields.Many2one('stock.location', string='Production location',
                                       domain=[('usage', '=', 'production')], required=True, )

    company_id = fields.Many2one('res.company', 'Company', required=True, default=lambda self: self.env.user.company_id)

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    def get_cod_fiscal(self, partner):
        if partner.is_company:
            cod_fiscal = partner.vat or ''
            vat_subjected = partner.vat_subjected or ('RO' in cod_fiscal)
            cod_fiscal = ''.join([s for s in cod_fiscal if s.isdigit()])
            if cod_fiscal:
                if vat_subjected:
                    country_code = partner.country_id.code or 'RO'
                    cod_fiscal = country_code + cod_fiscal
            else:
                cod_fiscal = "id_%s" % str(partner.id)
        else:
            if partner.cnp:
                cod_fiscal = partner.cnp
                cod_fiscal = ''.join([s for s in cod_fiscal if s.isdigit()])
            else:
                cod_fiscal = "id_%s" % str(partner.id)
        return cod_fiscal

    # conversie cont Odoo in cont Mentor
    def get_cont(self, account_id):
        if not account_id:
            return ''
        cont = account_id.code.replace('.', '')
        while cont[-1] == '0':
            cont = cont[:-1]
        if len(cont) > 3:
            cont = cont[:2] + '.0'.join(cont[2:])
        return cont

    def get_date(self, date):
        date = fields.Date.from_string(date)
        ##return date[8:10] + '.' + date[5:7] + '.' + date[:4]
        return date.strftime(self.format_data)

    def get_product_uom(self, product):
        uom = product.categ_id.mentor_uom_id or product.uom_id
        return uom

    def get_uom_ref(self, uom):
        uom_reg = self.env['product.uom'].search([('category_id', '=', uom.category_id.id),
                                                  ('uom_type', '=', 'reference')], limit=1)
        return uom_reg

    def get_product_code(self, product):
        return product.default_code or product.product_tmpl_id.default_code or 'ID_' + str(product.id)

    def get_doc_number(self, nume):
        NrDoc = nume or ''
        Serie = ''
        if '/' in NrDoc:
            seg = NrDoc.split('/')
            NrDoc = seg[-1]
            Serie = '/'.join(seg[:-1])
        elif '.' in NrDoc:
            seg = NrDoc.split('.')
            NrDoc = seg[-1]
            Serie = '.'.join(seg[:-1])
        else:
            Serie = nume or ''
            Serie = ''.join([s for s in Serie if not s.isdigit()])

        NrDoc = ''.join([s for s in NrDoc[-10:] if s.isdigit()])
        return NrDoc, Serie

    def get_uom(self, uom):
        cod_uom = uom.name or ''
        cod_uom = cod_uom.replace(' ', '')
        cod_uom = cod_uom.replace('(', '')
        cod_uom = cod_uom.replace(')', '')
        cod_uom = cod_uom[:10]
        return cod_uom

    def get_gestiune(self, product):
        gestiune = product.categ_id.gestiune_mentor
        if not gestiune:
            gestiune = self.location_id.code or str(self.prod_location_id.id)
        return gestiune

    @api.model
    def set_luna_lucru(self, pachet):
        pachet.update({
            'AnLucru': self.date_to[:4],
            'LunaLucru': self.date_to[5:7],
        })

    def get_temp_file(self, data):
        dicritics = {
            'ă': 'a', 'â': 'a',
            'ș': 's',
            'ț': 't',
            'î': 'i',
            'Ă': 'A', 'Â': 'A',
            'Ș': 'S',
            'Ț': 'T',
            'Î': 'I'
        }
        temp_file = StringIO()
        data.write(temp_file)
        txt = temp_file.getvalue()
        txt = txt.replace('\n', '\r\n')
        txt = txt.replace('False', '')
        txt = txt.replace(' = ', '=')
        txt = txt.replace(' = ', '=')
        for key, val in dicritics.items():
            txt = txt.replace(key, val)

        temp_file.seek(0)
        temp_file.truncate(0)
        temp_file.write(txt)
        temp_file = temp_file.getvalue().encode('ascii', 'ignore')
        return temp_file

    @api.model
    def do_export_parteneri(self, partner_ids):
        result_html = ''
        parteneri = configparser.ConfigParser()
        parteneri.optionxform = lambda option: option
        for partner in partner_ids:
            cod_fiscal = self.get_cod_fiscal(partner)
            if not partner:
                error = _("Partenerul %s nu are cod fiscal") % partner.name
                result_html += '<div>Eroare %s</div>' % error

            sections_name = "ParteneriNoi_%s" % cod_fiscal
            if '_id_' in sections_name:
                cod_fiscal = ''

            if partner.is_company:
                PersoanaFizica = 'NU'
            else:
                PersoanaFizica = 'DA'
            parteneri[sections_name] = {
                'Denumire': partner.name,
                'Tara': partner.country_id.name,
                'Judet': partner.state_id.code,
                'Adresa': partner.street,
                'Localitate': partner.city,
                'Sediu': '',
                'Telefon': partner.phone,
                'Email': partner.email,
                'CodFiscal': cod_fiscal,
                'RegistruComert': partner.nrc,
                'PersoanaFizica': PersoanaFizica
            }
        temp_file = self.get_temp_file(parteneri)

        return temp_file, result_html

    @api.model
    def do_export_articole(self, product_ids):
        result_html = ''
        articole = configparser.ConfigParser()
        articole.optionxform = lambda option: option

        for product in product_ids:
            code = self.get_product_code(product)
            proc_tva = 19

            if product.supplier_taxes_id:
                proc_tva = int(product.supplier_taxes_id.amount)

            sections_name = "ArticoleNoi_%s" % code
            articole[sections_name] = {
                'Denumire': product.name,
                'Serviciu': product.type != 'product' and 'D' or 'N',
                'GestiuneImplicita': self.get_gestiune(product),
                'ProcTVA': proc_tva
            }
            if product.type != 'product':
                articole[sections_name].update({
                    'ContServiciu': self.get_cont(product.categ_id.property_account_expense_categ_id),
                })
            else:
                articole[sections_name].update({
                    'TipContabil': product.categ_id.tip_contabil or '',
                })

        temp_file = self.get_temp_file(articole)
        return temp_file, result_html

    @api.model
    def do_export_intrari(self, invoice_in_ids):
        result_html = ''
        intrari = configparser.ConfigParser()
        intrari.optionxform = lambda option: option

        intrari['InfoPachet'] = {
            'TipDocument': 'FACTURA INTRARE',
            'TotalFacturi': len(invoice_in_ids)
        }
        self.set_luna_lucru(intrari['InfoPachet'])

        index = 1
        for invoice in invoice_in_ids:
            cod_fiscal = self.get_cod_fiscal(invoice.commercial_partner_id)

            sections_name = 'Factura_%s' % index
            if invoice.reference:
                NrDoc = invoice.reference
            else:
                NrDoc = invoice.number

            # Atentie Mentorul accepta doar 10 cifre la numar
            NrDoc, Serie = self.get_doc_number(NrDoc)

            if invoice.currency_id.name != "RON":
                Moneda = invoice.currency_id.name
                Curs = invoice.currency_id._get_rates(invoice.company_id, invoice.date_invoice)
                if Curs:
                    Curs = 1 / Curs[1]
                else:
                    Curs = 0
                Curs = str(Curs)
            else:
                Moneda = ''
                Curs = ''

            intrari[sections_name] = {
                'NrDoc': NrDoc,
                'Data': self.get_date(invoice.date_invoice),
                'CodFurnizor': cod_fiscal,
                'TVAINCASARE': '',  # todo: determinare
                'PRORATA': '',
                'Moneda': Moneda,  # invoice.currency_id.name,
                'Curs': Curs,
                'Scadenta': self.get_date(invoice.date_due),
                'Majorari': '',
                'Observatii': '',
                'Discount': '',
                'TotalArticole': len(invoice.invoice_line_ids)
            }
            sections_name = 'Items_%s' % index
            intrari[sections_name] = {}
            item = 0
            sign = invoice.type == 'in_refund' and -1 or 1

            linii_factura = {}
            for line in invoice.invoice_line_ids:
                code = self.get_product_code(line.product_id)
                if not code:
                    error = _("Produsul %s nu are cod") % line.product_id.name
                    result_html += '<div>Eroare %s</div>' % error

                if line.product_id.type == 'product':
                    cont = self.get_cont(line.account_id)
                    gestiune = self.get_gestiune(line.product_id)
                else:
                    gestiune = ''
                    cont = self.get_cont(line.account_id)

                line_index = code + cont + str(line.discount)
                tva = line.price_total - line.price_subtotal

                if line_index not in linii_factura:
                    mentor_uom_id = self.get_product_uom(line.product_id)

                    if line.uom_id != mentor_uom_id:
                        qty = sign * line.uom_id._compute_quantity(line.quantity, mentor_uom_id)
                        price = line.uom_id._compute_price(line.price_unit, mentor_uom_id)
                    else:
                        qty = sign * line.quantity
                        price = line.price_unit

                    linii_factura[line_index] = {
                        'code': code,
                        'qty': qty,
                        'price': price,
                        'mentor_uom_id': mentor_uom_id,
                        'cont': cont,
                        'discount': line.discount,
                        'gestiune': gestiune,
                        'tva': tva
                    }
                else:
                    mentor_uom_id = linii_factura[line_index]['mentor_uom_id']
                    if line.uom_id != mentor_uom_id:
                        qty = sign * line.uom_id._compute_quantity(line.quantity, mentor_uom_id)
                        price = line.uom_id._compute_price(line.price_unit, mentor_uom_id)

                    linii_factura[line_index]['price'] = (price + linii_factura[line_index]['price']) / 2
                    linii_factura[line_index]['qty'] += qty
                    linii_factura[line_index]['tva'] += tva

            for line_index in linii_factura:
                item += 1
                intrari[sections_name]['Item_%s' % item] = ';'.join([
                    linii_factura[line_index]['code'],  # Cod intern/extern articol;
                    self.get_uom(linii_factura[line_index]['mentor_uom_id']),
                    str(linii_factura[line_index]['qty']),
                    str(linii_factura[line_index]['price']),  # line., price_unit_without_taxes
                    linii_factura[line_index]['gestiune'],  # Simbol gestiune: pentru receptie/repartizare cheltuieli
                    str(linii_factura[line_index]['discount']),  # Discount linie
                    linii_factura[line_index]['cont'],  # Simbol cont articol serviciu;
                    '',  # Pret inregistrare;
                    '',  # Termen garantie;
                    '',  # Valoare suplimentara;
                    ''  # Observatii la nivel articol;
                ])

                intrari[sections_name]['Item_%s_TVA' % item] = str(linii_factura[line_index]['tva'])

            # for line in invoice.invoice_line_ids:
            #     item += 1
            #     code = self.get_product_code(line.product_id)
            #     if not code:
            #         error = _("Produsul %s nu are cod") % line.product_id.name
            #         result_html += '<div>Eroare %s</div>' % error
            #
            #     if line.product_id.type == 'product':
            #         cont = self.get_cont(line.account_id)
            #         gestiune = self.get_gestiune(line.product_id)
            #     else:
            #         gestiune = ''
            #         cont = self.get_cont(line.account_id)
            #
            #     qty = line.quantity * sign
            #     price = line.price_unit
            #     tva = line.price_total - line.price_subtotal
            #
            #     mentor_uom_id = self.get_product_uom(line.product_id)
            #     if line.uom_id != mentor_uom_id:
            #         qty = sign * line.uom_id._compute_quantity(line.quantity, mentor_uom_id)
            #         price = line.uom_id._compute_price(line.price_unit, mentor_uom_id)
            #         # TVA  nu mai trebuie recalculat ca este pe totla linie si nu mai conteaza cantitatea si unitatea de masura.
            #         # tva = line.uom_id._compute_price(tva, mentor_uom_id)
            #     else:
            #         qty = sign * line.quantity
            #         price = line.price_unit
            #
            #     code = self.get_product_code(line.product_id)
            #     intrari[sections_name]['Item_%s' % item] = ';'.join([
            #         code,  # Cod intern/extern articol;
            #         self.get_uom(mentor_uom_id),
            #
            #         str(qty),
            #         str(price),  # line., price_unit_without_taxes
            #         gestiune,  # Simbol gestiune: pentru receptie/repartizare cheltuieli
            #         str(line.discount),  # Discount linie
            #         cont,  # Simbol cont articol serviciu;
            #         '',  # Pret inregistrare;
            #         '',  # Termen garantie;
            #         '',  # Valoare suplimentara;
            #         ''  # Observatii la nivel articol;
            #     ])
            #
            #     intrari[sections_name]['Item_%s_TVA' % item] = str(tva)
            #
            #     # if line.uom_id.id != line.product_id.uom_id.id:
            #     #     qty = sign * line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
            #     #     intrari[sections_name]['Item_%s_UM1' % item] = str(qty)

            index += 1

        temp_file = self.get_temp_file(intrari)

        return temp_file, result_html

    @api.model
    def do_export_intrari_import(self, invoice_in_import_ids):
        result_html = ''
        intrari = configparser.ConfigParser()
        intrari.optionxform = lambda option: option

        intrari['InfoPachet'] = {
            'TipDocument': 'INVOICE',
            'TotalFacturi': len(invoice_in_import_ids)
        }
        self.set_luna_lucru(intrari['InfoPachet'])

        index = 1
        for invoice in invoice_in_import_ids:
            cod_fiscal = self.get_cod_fiscal(invoice.commercial_partner_id)

            sections_name = 'Factura_%s' % index
            if invoice.reference:
                NrDoc = invoice.reference
            else:
                NrDoc = invoice.number

            # Atentie Mentorul accepta doar 10 cifre la numar
            NrDoc, Serie = self.get_doc_number(NrDoc)

            if invoice.currency_id.name != "RON":
                Moneda = invoice.currency_id.name
                Curs = invoice.currency_id._get_rates(invoice.company_id, invoice.date_invoice)
                if Curs:
                    Curs = 1 / Curs[1]
                else:
                    Curs = 0
                Curs = str(Curs)
            else:
                Moneda = ''
                Curs = ''

            intrari[sections_name] = {
                'NrDoc': NrDoc,
                'Data': self.get_date(invoice.date_invoice),
                'Lohn': '',
                'CodFurnizor': cod_fiscal,
                'Moneda': Moneda,  # invoice.currency_id.name,
                'Curs': Curs,
                'Scadenta': self.get_date(invoice.date_due),
                'Majorari': '',
                'Observatii': '',
                'Discount': '',
                'TotalArticole': len(invoice.invoice_line_ids),
                'TaxareInversa': '',
            }

            sections_name = 'DVI_%s' % index

            intrari[sections_name] = {
                'NrDoc': NrDoc,
                'Data': self.get_date(invoice.date_invoice),
                'CodVama': cod_fiscal,
                'Curs': Curs,
            }

            sections_name = 'Items_%s' % index
            intrari[sections_name] = {}
            item = 0
            sign = invoice.type == 'in_refund' and -1 or 1

            for line in invoice.invoice_line_ids:
                item += 1
                code = self.get_product_code(line.product_id)
                if not code:
                    error = _("Produsul %s nu are cod") % line.product_id.name
                    result_html += '<div>Eroare %s</div>' % error

                if line.product_id.type == 'product':
                    cont = self.get_cont(line.account_id)
                    gestiune = self.get_gestiune(line.product_id)
                else:
                    gestiune = ''
                    cont = self.get_cont(line.account_id)

                qty = line.quantity * sign
                price = line.price_unit
                tva = line.price_total - line.price_subtotal

                mentor_uom_id = self.get_product_uom(line.product_id)
                if line.uom_id != mentor_uom_id:
                    qty = sign * line.uom_id._compute_quantity(line.quantity, mentor_uom_id)
                    price = line.uom_id._compute_price(line.price_unit, mentor_uom_id)
                    # TVA  nu mai trebuie recalculat ca este pe totla linie si nu mai conteaza cantitatea si unitatea de masura.
                    # tva = line.uom_id._compute_price(tva, mentor_uom_id)
                else:
                    qty = sign * line.quantity
                    price = line.price_unit

                code = self.get_product_code(line.product_id)
                intrari[sections_name]['Item_%s' % item] = ';'.join([
                    code,  # Cod intern/extern articol;
                    self.get_uom(mentor_uom_id),

                    str(qty),
                    str(price),  # line., price_unit_without_taxes
                    gestiune,  # Simbol gestiune: pentru receptie/repartizare cheltuieli
                    str(line.discount),  # Discount linie
                    cont,  # Simbol cont articol serviciu;
                    '',  # Pret inregistrare;
                    '',  # Termen garantie;
                    '',  # Valoare suplimentara;
                    ''  # Observatii la nivel articol;
                ])

                intrari[sections_name]['Item_%s_TVA' % item] = str(tva)

                # if line.uom_id.id != line.product_id.uom_id.id:
                #     qty = sign * line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                #     intrari[sections_name]['Item_%s_UM1' % item] = str(qty)

            index += 1

        temp_file = self.get_temp_file(intrari)

        return temp_file, result_html

    @api.model
    def do_export_bonuri_intrari(self, voucher_in_ids):
        result_html = ''
        intrari = configparser.ConfigParser()
        intrari.optionxform = lambda option: option

        intrari['InfoPachet'] = {
            'TipDocument': 'BON FISCAL INTRARE',
            'TotalBonuri': len(voucher_in_ids)
        }
        self.set_luna_lucru(intrari['InfoPachet'])
        index = 1
        for voucher in voucher_in_ids:
            cod_fiscal = self.get_cod_fiscal(voucher.partner_id)

            sections_name = 'Bon_%s' % index
            if voucher.reference:
                NrDoc = voucher.reference
            else:
                NrDoc = voucher.number
            # Mentorul accepta doar 10 cifre la numar

            NrDoc, Serie = self.get_doc_number(NrDoc)

            intrari[sections_name] = {
                'NrDoc': NrDoc,
                'Data': self.get_date(voucher.date),
                'CodFurnizor': cod_fiscal,
                'TotalArticole': len(voucher.line_ids)
            }
            sections_name = 'Items_%s' % index
            intrari[sections_name] = {}
            item = 0
            sign = 1

            for line in voucher.line_ids:
                item += 1
                code = self.get_product_code(line.product_id)
                if not code:
                    error = _("Produsul %s nu are cod") % line.product_id.name
                    result_html += '<div>Eroare %s</div>' % error

                if line.product_id.type == 'product':
                    cont = self.get_cont(line.account_id)
                    gestiune = self.get_gestiune(line.product_id)
                else:
                    gestiune = ''
                    cont = self.get_cont(line.account_id)

                mentor_uom_id = self.get_product_uom(line.product_id)  #
                qty = sign * line.quantity
                price = line.price_unit

                # if line.uom_id != mentor_uom_id:
                #     qty = sign * line.uom_id._compute_quantity(line.quantity, mentor_uom_id)
                #     price = line.uom_id._compute_price(line.price_unit, mentor_uom_id)
                # else:
                #     qty = sign * line.quantity
                #     price = line.price_unit

                if line.tax_ids:
                    taxes = line.tax_ids.compute_all(line.price_unit, quantity=line.quantity, product=line.product_id)
                    tva = taxes['total_included'] - taxes['total_excluded']
                else:
                    tva = 0
                # tva = line.price_total - line.price_subtotal
                code = self.get_product_code(line.product_id)
                intrari[sections_name]['Item_%s' % item] = ';'.join([
                    code,  # Cod intern/extern articol;
                    self.get_uom(line.product_id.uom_id),

                    str(qty),
                    str(price),  # line., price_unit_without_taxes
                    gestiune,  # Simbol gestiune: pentru receptie/repartizare cheltuieli
                    '0',  # Discount linie
                    cont,  # Simbol cont articol serviciu;
                    '',  # Pret inregistrare;
                    '',  # Termen garantie;
                    '',  # Valoare suplimentara;
                    ''  # Observatii la nivel articol;
                ])
                intrari[sections_name]['Item_%s_TVA' % item] = str(tva)
                # if line.uom_id.id != line.product_id.uom_id.id:
                #     qty = sign * line.uom_id._compute_quantity(line.quantity, line.product_id.uom_id)
                #     intrari[sections_name]['Item_%s_UM1' % item] = str(qty)

            index += 1

        temp_file = self.get_temp_file(intrari)

        return temp_file, result_html

    @api.model
    def do_export_iesiri(self, invoice_out_ids):
        result_html = ''
        iesiri = configparser.ConfigParser()
        iesiri.optionxform = lambda option: option

        iesiri['InfoPachet'] = {
            'TipDocument': 'FACTURA IESIRE',
            'TotalFacturi': len(invoice_out_ids)
        }

        self.set_luna_lucru(iesiri['InfoPachet'])
        index = 1
        for invoice in invoice_out_ids:
            cod_fiscal = self.get_cod_fiscal(invoice.commercial_partner_id)

            sections_name = 'Factura_%s' % index

            NrDoc, SerieCarnet = self.get_doc_number(
                invoice.number or invoice.move_name)  # daca facutra e anulata numarul ei se gaseste in move_name

            if invoice.journal_id.serie_carnet:
                SerieCarnet = invoice.journal_id.serie_carnet

            iesiri[sections_name] = {
                'SerieCarnet': SerieCarnet,
                'NrDoc': NrDoc,
                'Data': self.get_date(invoice.date_invoice),
                'CodClient': cod_fiscal,
                'TVAINCASARE': '',  # todo: determinare
                'TotalArticole': len(invoice.invoice_line_ids),
                'TaxareInversa': 'N',
                'Scadenta': self.get_date(invoice.date_due)
            }
            sections_name = 'Items_%s' % index
            iesiri[sections_name] = {}
            item = 0
            sign = invoice.type == 'out_refund' and -1 or 1
            for line in invoice.invoice_line_ids:
                item += 1
                code = self.get_product_code(line.product_id)
                if not code:
                    error = _("Produsul %s nu are cod") % line.product_id.name
                    result_html += '<div>Eroare %s</div>' % error
                if line.product_id.type == 'product':
                    gestiune = self.get_gestiune(line.product_id)
                else:
                    gestiune = ''

                mentor_uom_id = self.get_product_uom(line.product_id)
                if line.uom_id != mentor_uom_id:
                    qty = sign * line.uom_id._compute_quantity(line.quantity, mentor_uom_id)
                    price = line.uom_id._compute_price(line.price_unit, mentor_uom_id)
                else:
                    qty = sign * line.quantity
                    price = line.price_unit

                code = self.get_product_code(line.product_id)
                if self.without_discount:
                    discount = ''
                    price = price * (1 - (line.discount or 0.0) / 100.0)
                else:
                    discount = str(line.discount)

                iesiri[sections_name]['Item_%s' % item] = ';'.join([
                    code,  # Cod intern/extern articol;
                    self.get_uom(mentor_uom_id),

                    str(qty),
                    str(price),  # line., price_unit_without_taxes
                    gestiune,  # Simbol gestiune: pentru receptie/repartizare cheltuieli
                    discount,  # Discount linie

                    '',  # Pret inregistrare;
                    '',  # Observatii la nivel articol;
                    '',  # Pret de achizitie
                ])
                if line.product_id.type != 'product':
                    iesiri[sections_name]['Item_%s_Ext' % item] = ';'.join([
                        gestiune,
                        self.get_cont(line.account_id),  # Simbol cont articol serviciu;
                    ])
            index += 1

        temp_file = self.get_temp_file(iesiri)
        return temp_file, result_html

    def do_export_bonuri_consum(self, move_ids):
        result_html = ''
        bonuri = configparser.ConfigParser()
        bonuri.optionxform = lambda option: option
        locations = {}

        for move in move_ids:
            if move.location_dest_id != self.prod_location_id:  #
                sign = -1
                location_id = move.location_dest_id
            else:
                sign = 1
                location_id = move.location_id

            if location_id.id not in locations:
                locations[location_id.id] = {'lines': {}, 'location_id': location_id}
            lines = locations[location_id.id]['lines']

            price_unit = move.price_unit
            if move.product_id.cost_method == 'standard':
                price_unit = move.product_id.standard_price

            if not move.product_id.id in lines:
                lines[move.product_id.id] = {
                    'product_id': move.product_id,
                    'qty': sign * move.product_qty,
                    'amount': sign * price_unit * move.product_qty
                }
            else:
                lines[move.product_id.id]['qty'] += sign * move.product_qty
                lines[move.product_id.id]['amount'] += sign * price_unit * move.product_qty

        bonuri['InfoPachet'] = {
            'TipDocument': 'BON DE CONSUM',
            'TotalBonuri': len(locations)
        }
        self.set_luna_lucru(bonuri['InfoPachet'])

        GestConsum = self.prod_location_id.code or str(self.prod_location_id.id)
        index = 0
        for location_id in locations:
            index += 1
            location = locations[location_id]
            lines = location['lines']
            sections_name = 'Bon_%s' % index
            bonuri[sections_name] = {
                'NrDoc': self.date_to[:4] + self.date_to[5:7] + str(index),
                'Data': self.get_date(self.date_to),
                'GestConsum': GestConsum,
                'TotalArticole': len(lines)
            }

            item = 0

            gest = location['location_id'].code or str(location['location_id'].id)
            sections_name = 'Items_%s' % index
            bonuri[sections_name] = {}
            for product_id in lines:
                line = lines[product_id]
                product = line['product_id']

                item += 1
                qty = line['qty']
                if qty:
                    price = -1 * line['amount'] / qty
                else:
                    price = 0.0

                mentor_uom_id = self.get_product_uom(product)
                if product.uom_id != mentor_uom_id:
                    qty = product.uom_id._compute_quantity(qty, mentor_uom_id)
                    price = product.uom_id._compute_price(price, mentor_uom_id)

                code = self.get_product_code(line['product_id'])
                bonuri[sections_name]['Item_%s' % item] = ';'.join([
                    code,  # Cod intern/extern articol;
                    self.get_uom(mentor_uom_id),
                    str(qty),
                    str(price),
                    gest
                ])

        temp_file = self.get_temp_file(bonuri)
        return temp_file, result_html

    def do_export_note_predari(self, move_ids):
        result_html = ''
        predari = configparser.ConfigParser()
        predari.optionxform = lambda option: option
        locations = {}

        for move in move_ids:
            if move.location_id != self.prod_location_id:  #
                sign = -1
                location_dest_id = move.location_id
            else:
                sign = 1
                location_dest_id = move.location_dest_id

            if location_dest_id.id not in locations:
                locations[location_dest_id.id] = {'lines': {}, 'location_id': location_dest_id}
            lines = locations[location_dest_id.id]['lines']

            price_unit = move.price_unit
            if move.product_id.cost_method == 'standard':
                price_unit = move.product_id.standard_price

            if not move.product_id.id in lines:
                lines[move.product_id.id] = {
                    'product_id': move.product_id,
                    'qty': sign * move.product_qty,
                    'amount': sign * price_unit * move.product_qty
                }
            else:
                lines[move.product_id.id]['qty'] += sign * move.product_qty
                lines[move.product_id.id]['amount'] += sign * price_unit * move.product_qty

        predari['InfoPachet'] = {
            'TipDocument': 'NOTA PREDARE',
            'TotalNote': len(locations)
        }
        self.set_luna_lucru(predari['InfoPachet'])

        Gestsursa = self.prod_location_id.code or str(self.prod_location_id.id)
        index = 0
        for location_id in locations:
            index += 1
            location = locations[location_id]
            lines = location['lines']
            sections_name = 'Nota_%s' % index
            predari[sections_name] = {
                'NrDoc': self.date_to[:4] + self.date_to[5:7] + str(index),
                'Data': self.get_date(self.date_from),
                'Gestsursa': Gestsursa,
                'TotalArticole': len(lines)
            }

            item = 0

            gest = location['location_id'].code or str(location['location_id'].id)
            sections_name = 'Items_%s' % index
            predari[sections_name] = {}
            for product_id in lines:
                line = lines[product_id]
                product = line['product_id']
                item += 1
                qty = line['qty']
                if qty:
                    price = line['amount'] / line['qty']
                else:
                    price = 0
                mentor_uom_id = self.get_product_uom(product)
                if product.uom_id != mentor_uom_id:
                    qty = product.uom_id._compute_quantity(qty, mentor_uom_id)
                    price = product.uom_id._compute_price(price, mentor_uom_id)

                code = self.get_product_code(line['product_id'])
                predari[sections_name]['Item_%s' % item] = ';'.join([
                    code,  # Cod intern/extern articol;
                    self.get_uom(mentor_uom_id),
                    str(qty),
                    str(price),
                    gest
                ])

        temp_file = self.get_temp_file(predari)
        return temp_file, result_html

    def do_export_gestiuni(self, location_ids):
        result_html = ''
        gestiuni = configparser.ConfigParser()
        gestiuni.optionxform = lambda option: option
        for location in location_ids:
            code = location.code or str(location.id)
            gestiuni['GestiuniNoi_%s' % code] = {
                'Denumire': location.name or ''
            }
        temp_file = self.get_temp_file(gestiuni)
        return temp_file, result_html

    def do_export_plati(self, plati_ids):
        result_html = ''
        plati = configparser.ConfigParser()
        plati.optionxform = lambda option: option
        plati['InfoPachet'] = {
            'TotalDocumente': len(plati_ids)
        }
        self.set_luna_lucru(plati['InfoPachet'])
        item = 0
        for plata in plati_ids:
            item += 1

            NrDoc, Serie = self.get_doc_number(plata.name)

            if plata.journal_id.type == 'cash':
                sursa = 'CASA'
            elif plata.journal_id.type == 'bank':
                sursa = 'BANCA'
            else:
                sursa = 'AVANS DECONTARE'

            cod_fiscal = self.get_cod_fiscal(plata.partner_id)

            plati['Document%s' % item] = {
                'Sursa': sursa,

                'NumeBanca': plata.partner_bank_account_id.bank_name or 'NA',
                'SimbolBanca': plata.partner_bank_account_id.bank_bic or 'NA',
                'NumeCont': plata.journal_id.name or 'NA',
                'NrCont': plata.partner_bank_account_id.sanitized_acc_number or 'NA',
                'LocalitateCont': 'NA',
                'ZiuaPlatii': str(plata.payment_date.day),
                'TotalPlati': '1',

            }
            NrFactura = 'NA'
            SerieFactura = 'NA'
            for invoice in plata.invoice_ids:
                NrFactura, SerieFactura = self.get_doc_number(invoice.number)

            plati['Document%s-Plata1' % item] = {
                'DocPlata': 'CD',
                # Reprezinta=tip (poate lua una din valorile: PLATA FACTURA,PLATA PENALITATI,ALIMENTARE CREDIT, DIMINUARE CREDIT, PERSONAL ANGAJAT)
                'Reprezinta': 'PLATA FACTURA',
                'NrFactura': NrFactura,
                'SerieCarnet': SerieFactura,
                'NrDocument': NrDoc,
                'ValPlatita': str(plata.amount),
                'Furnizor': plata.partner_id.name,
                'CodFurnizor': cod_fiscal
            }

        temp_file = self.get_temp_file(plati)
        return temp_file, result_html

    def do_export_incasari(self, incasari_ids):
        result_html = ''
        incasari = configparser.ConfigParser()
        incasari.optionxform = lambda option: option
        incasari['InfoPachet'] = {
            'TotalDocumente': len(incasari_ids)
        }
        self.set_luna_lucru(incasari['InfoPachet'])
        item = 0
        for incasare in incasari_ids:
            item += 1

            NrDoc, Serie = self.get_doc_number(incasare.name)

            if incasare.journal_id.type == 'cash':
                sursa = 'CASA'
            elif incasare.journal_id.type == 'bank':
                sursa = 'BANCA'
            else:
                sursa = 'AVANS DECONTARE'

            cod_fiscal = self.get_cod_fiscal(incasare.partner_id)

            incasari['Document%s' % item] = {
                'Sursa': sursa,

                'NumeBanca': incasare.partner_bank_account_id.bank_name or 'NA',
                'SimbolBanca': incasare.partner_bank_account_id.bank_bic or 'NA',
                'NumeCont': incasare.journal_id.name or 'NA',
                'NrCont': incasare.partner_bank_account_id.sanitized_acc_number or 'NA',
                'LocalitateCont': 'NA',
                'ZiuaIncasarii': str(incasare.payment_date.day),
                'TotalIncasari': '1',

            }
            NrFactura = 'NA'
            SerieFactura = 'NA'
            for invoice in incasare.invoice_ids:
                NrFactura, SerieFactura = self.get_doc_number(invoice.number)

            incasari['Document%s-Incasare1' % item] = {
                'DocPlata': 'CD',
                'Reprezinta': 'INCASARE FACTURA',
                'SerieCarnet': SerieFactura,
                'NrFactura': NrFactura,
                'NrDocument': NrDoc,
                'ValIncsata': str(incasare.amount),
                'Furnizor': incasare.partner_id.name,
                'CodFurnizor': cod_fiscal
            }

        temp_file = self.get_temp_file(incasari)
        return temp_file, result_html

    def do_export_avize(self, avize_ids):
        result_html = ''
        avize = configparser.ConfigParser()
        avize.optionxform = lambda option: option
        avize['InfoPachet'] = {
            'TotalAvize': len(avize_ids),
            'Tipdocument': 'AVIZ EXPEDITIE',
        }
        self.set_luna_lucru(avize['InfoPachet'])
        index = 0
        for picking in avize_ids:
            index += 1
            NrDoc, Serie = self.get_doc_number(picking.name)
            cod_fiscal = self.get_cod_fiscal(picking.partner_id)
            avize['Aviz_%s' % index] = {
                'NrDoc': NrDoc,
                'Data': self.get_date(picking.date),
                'CodClient': cod_fiscal,
                'TotalArticole': len(picking.move_ids)
            }
            sections_name = 'Items_%s' % index
            avize[sections_name] = {}
            item = 0

            for move in picking.move_ids:
                item += 1
                code = self.get_product_code(move.product_id)
                gest = move.location_id.code or str(move.location_id.id)

                qty = move.product_qty
                price = 0.0  # trebuie determinat pretul din comanda de vanzare

                line = move.sale_line_id
                if line:
                    taxes_ids = line.tax_id
                    incl_tax = taxes_ids.filtered(lambda tax: tax.price_include)
                    if line.product_uom_qty != 0:
                        price = line.price_subtotal / line.product_uom_qty
                        if incl_tax:
                            price = line.price_total / line.product_uom_qty

                if not price:
                    price = move.product_id.list_price

                mentor_uom_id = self.get_product_uom(move.product_id)
                if move.product_id.uom_id != mentor_uom_id:
                    qty = move.product_id.uom_id._compute_quantity(qty, mentor_uom_id)
                    price = move.product_id.uom_id._compute_price(price, mentor_uom_id)

                avize[sections_name]['Item_%s' % item] = ';'.join([
                    code,  # Cod intern/extern articol;
                    self.get_uom(mentor_uom_id),
                    str(qty),
                    str(price),
                    gest
                ])

        temp_file = self.get_temp_file(avize)
        return temp_file, result_html

    @api.multi
    def do_export(self):

        buff = BytesIO()

        files = []

        # This is my zip file
        zip_archive = zipfile.ZipFile(buff, mode='w')
        # zip_archive.comment = 'Arhiva pentru Mentor'

        partner_ids = self.env['res.partner']
        partner_in_ids = self.env['res.partner']
        partner_out_ids = self.env['res.partner']
        product_ids = self.env['product.product']
        move_id_ids = self.env['stock.move']
        move_out_ids = self.env['stock.move']
        move_consum = self.env['stock.move']
        move_predare = self.env['stock.move']

        # de adaugat conditia pentru moneda
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', 'in', ['open', 'paid']),  # NU se trimit si facturile anulate!
            ('type', 'in', ['in_invoice', 'in_refund']),
            ('company_id', '=', self.company_id.id)
        ]

        if self.journal_ids:
            domain += [('journal_id', 'in', self.journal_ids.ids)]

        invoice_ids = self.env['account.invoice'].search(domain)

        invoice_in_ids = self.env['account.invoice']
        invoice_in_import_ids = self.env['account.invoice']

        ro_country = self.env.ref('base.ro')
        for invoice in invoice_ids:
            if not invoice.commercial_partner_id.country_id or invoice.commercial_partner_id.country_id == ro_country:
                invoice_in_ids |= invoice
            else:
                invoice_in_import_ids |= invoice

        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', 'in', ['posted']),
            ('voucher_type', 'in', ['purchase']),
            ('company_id', '=', self.company_id.id)
        ]
        if self.journal_ids:
            domain += [('journal_id', 'in', self.journal_ids.ids)]
        voucher_in_ids = self.env['account.voucher'].search(domain)

        for invoice in invoice_ids:
            for line in invoice.invoice_line_ids:
                product_ids |= line.product_id

        for invoice in invoice_ids:
            partner_in_ids |= invoice.commercial_partner_id

        for voucher in voucher_in_ids:
            partner_in_ids |= voucher.partner_id.commercial_partner_id
            for line in voucher.line_ids:
                product_ids |= line.product_id

        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', 'in', ['open', 'paid', 'cancel']),  # se trimit si facturile anulate!
            ('type', 'in', ['out_invoice', 'out_refund']),
            ('company_id', '=', self.company_id.id)
        ]
        if self.journal_ids:
            domain += [('journal_id', 'in', self.journal_ids.ids)]
        invoice_out_ids = self.env['account.invoice'].search(domain)

        for invoice in invoice_out_ids:
            for line in invoice.invoice_line_ids:
                product_ids |= line.product_id

        for invoice in invoice_out_ids:
            partner_out_ids |= invoice.commercial_partner_id

        if self.prod_location_id:

            domain = [
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
                ('state', '=', 'done'),
                ('location_dest_id', '=', self.prod_location_id.id),
                ('company_id', '=', self.company_id.id)
            ]

            move_out_ids = self.env['stock.move'].search(domain)
            for move in move_out_ids:
                product_ids |= move.product_id
                if move.product_id.categ_id.way_production == 'receipt':
                    move_predare |= move
                else:
                    move_consum |= move

            domain = [
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
                ('state', '=', 'done'),
                ('location_id', '=', self.prod_location_id.id),
                ('company_id', '=', self.company_id.id)
            ]

            move_in_ids = self.env['stock.move'].search(domain)
            for move in move_in_ids:
                product_ids |= move.product_id
                if move.product_id.categ_id.way_production == 'consumption':
                    move_consum |= move
                else:
                    move_predare |= move

        domain = [
            ('payment_date', '>=', self.date_from),
            ('payment_date', '<=', self.date_to),
            ('state', '=', 'posted'),
            ('payment_type', '=', 'outbound'),
            ('company_id', '=', self.company_id.id)
        ]
        plati_ids = self.env['account.payment'].search(domain)

        domain = [
            ('payment_date', '>=', self.date_from),
            ('payment_date', '<=', self.date_to),
            ('state', '=', 'posted'),
            ('payment_type', '=', 'inbound'),
            ('company_id', '=', self.company_id.id)
        ]
        incasari_ids = self.env['account.payment'].search(domain)

        domain = [
            ('state', '=', 'done'),
            ('notice', '=', True),
            ('date_done', '>=', self.date_from),
            ('date_done', '<=', self.date_to),
            ('location_id', '=', self.location_id.id),
            ('company_id', '=', self.company_id.id)
        ]

        avize_ids = self.env['stock.picking'].search(domain)

        # export toate locatiile
        location_ids = self.env['stock.location'].search([])

        result_html = ' <div>Au fost exportate:</div>'
        result_html += '<div>Facturi de intrare: %s</div>' % str(len(invoice_in_ids))
        result_html += '<div>Facturi de intrare din Import: %s</div>' % str(len(invoice_in_import_ids))
        result_html += '<div>Bonuri fiscale: %s</div>' % str(len(voucher_in_ids))
        result_html += '<div>Facturi de iesire %s</div>' % str(len(invoice_out_ids))
        result_html += '<div>Produse %s</div>' % str(len(product_ids))
        result_html += '<div>Furnizori %s</div>' % str(len(partner_in_ids))

        result_html += '<div>Client %s</div>' % str(len(partner_out_ids))

        result_html += '<div>Consumuri %s</div>' % str(len(move_consum))
        result_html += '<div>Note Predari %s</div>' % str(len(move_predare))

        result_html += '<div>Plati %s</div>' % str(len(plati_ids))
        result_html += '<div>Incasari %s</div>' % str(len(incasari_ids))

        result_html += '<div>Avize de livrare %s</div>' % str(len(avize_ids))

        partner_ids = partner_in_ids | partner_out_ids
        temp_file, messaje = self.do_export_parteneri(partner_ids)

        result_html += messaje

        file_name = 'Partner.txt'
        zip_archive.writestr(file_name, temp_file)

        temp_file, messaje = self.do_export_articole(product_ids)
        result_html += messaje
        file_name = 'Articole.txt'
        zip_archive.writestr(file_name, temp_file)

        temp_file, messaje = self.do_export_intrari(invoice_in_ids)
        result_html += messaje
        file_name = 'Facturi_Intrare.txt'
        zip_archive.writestr(file_name, temp_file)

        temp_file, messaje = self.do_export_intrari_import(invoice_in_import_ids)
        result_html += messaje
        file_name = 'Facturi_Intrare din Import.txt'
        zip_archive.writestr(file_name, temp_file)

        temp_file, messaje = self.do_export_bonuri_intrari(voucher_in_ids)
        result_html += messaje
        file_name = 'Bonuri Fiscale Intrare.txt'
        zip_archive.writestr(file_name, temp_file)

        temp_file, messaje = self.do_export_iesiri(invoice_out_ids)
        result_html += messaje
        file_name = 'Facturi_Iesire.txt'
        zip_archive.writestr(file_name, temp_file)

        temp_file, messaje = self.do_export_bonuri_consum(move_consum)
        result_html += messaje
        file_name = 'Bonuri_consum.txt'
        zip_archive.writestr(file_name, temp_file)

        temp_file, messaje = self.do_export_note_predari(move_predare)
        result_html += messaje
        file_name = 'Note_Predari.txt'
        zip_archive.writestr(file_name, temp_file)

        temp_file, messaje = self.do_export_gestiuni(location_ids)
        result_html += messaje
        file_name = 'Gestiuni.txt'
        zip_archive.writestr(file_name, temp_file)

        # temp_file, messaje = self.do_export_plati(plati_ids)
        # result_html += messaje
        # file_name = 'Plati.txt'
        # zip_archive.writestr(file_name, temp_file)
        #
        # temp_file, messaje = self.do_export_incasari(incasari_ids)
        # result_html += messaje
        # file_name = 'Incasari.txt'
        # zip_archive.writestr(file_name, temp_file)

        # temp_file, messaje = self.do_export_avize(avize_ids)
        # result_html += messaje
        # file_name = 'Avize.txt'
        # zip_archive.writestr(file_name, temp_file)

        # Here you finish editing your zip. Now all the information is
        # in your buff StringIO object
        zip_archive.close()

        out = base64.encodebytes(buff.getvalue())
        buff.close()

        filename = 'ExportOdooMentor_%s_%s' % (self.date_from, self.date_to)
        extension = 'zip'

        name = "%s.%s" % (filename, extension)
        self.write({'state': 'get',
                    'data_file': out,
                    'name': name,
                    'result': result_html})

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'export.mentor',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
