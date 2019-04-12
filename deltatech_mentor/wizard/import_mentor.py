# coding=utf-8

import logging
import threading
import base64
import zipfile
from io import BytesIO
import configparser as ConfigParser
import unicodedata

from odoo import models, fields, api, _, registry


class import_mentor(models.TransientModel):
    _name = 'import.mentor'
    _description = "Export Mentor"

    data_file = fields.Binary(string='File')
    data_file_name = fields.Char(string='Mentor File Name')

    sel_articole = fields.Boolean('Articole')
    sel_partener = fields.Boolean('Partener')
    sel_gestiuni = fields.Boolean('Gestiuni')
    sel_retetar = fields.Boolean('Retetar')
    sel_nir = fields.Boolean('Nir')

    ignore_error = fields.Boolean(string='Ignore Errors', default=True)
    result = fields.Html(string="Result Export", readonly=True)

    state = fields.Selection([('choose', 'choose'),  # choose period
                              ('get', 'get')], default='choose')  # get the file

    def unaccent(self, text):

        text = str(text.decode('utf-8', 'ignore').encode("utf-8"))
        text = unicodedata.normalize('NFD', text)
        text = text.encode('ascii', 'ignore')
        text = text.decode("utf-8")
        text = text.replace(chr(13), ' ')
        text = text.replace('\n', ' ')
        return str(text)

    @api.multi
    def do_import(self):
        threaded_job = threading.Thread(target=self._do_import_job, args=())
        threaded_job.start()
        channel = self.env.ref('mail.channel_all_employees')
        ref = self.env.ref("mail.mt_comment")
        self.env['mail.message'].create({
            'model': 'mail.channel',
            'message_type': 'notification',
            'body': 'Import Mentor lansat in background',
            'res_id': channel.id,
            'subtype_id': ref.id
        })
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def _do_import_job(self):
        with api.Environment.manage():
            # As this function is in a new thread, i need to open a new cursor, because the old one may be closed
            new_cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=new_cr))  # TDE FIXME

            mentor_file = base64.decodestring(self.data_file)
            buff = BytesIO(mentor_file)
            self.zip_archive = zipfile.ZipFile(buff, mode='r')
            self.file_list = self.zip_archive.namelist()
            if self.sel_articole and 'Articole.txt' in self.file_list:
                data = self.zip_archive.open('Articole.txt')
                self.import_articole(data)
            if self.sel_retetar and 'retetar.txt' in self.file_list:
                data = self.zip_archive.open('retetar.txt')
                self.import_retetar(data)
            if self.sel_nir and 'nir.txt' in self.file_list:
                data = self.zip_archive.open('nir.txt')
                self.import_nir(data)
            self.zip_archive.close()
            buff.close()

            # close the new cursor
            self._cr.close()
            return {}

    def import_retetar(self, data):
        """
        [InfoPachet]
        AnLucru=2017
        LunaLucru=08
        TipDocument=RETETAR
        TotalProduse={nr}

        [Produs_{nr1}]
        CodProdus={cod}
        Denumire={denumire}
        Categorie={categorie}
        Departament={gest}
        CotaTVA={}
        TotalMaterii=1

        [Items_1]
        Item_1={cod};{cat};

        """
        p = ConfigParser.ConfigParser()
        p.readfp(data)
        item_count = int(p.get('InfoPachet', 'TotalProduse'))
        tax = {}
        coponente = {}
        categorii = {}
        for nr in range(1, item_count + 1):
            sec_p = 'Produs_%s' % nr
            sec_i = 'Items_%s' % nr
            CodProdus = p.get(sec_p, 'CodProdus')

            TotalMaterii = int(p.get(sec_p, 'TotalMaterii'))

            product = self.env['product.product'].search([('default_code', '=', CodProdus)], limit=1)
            if not product:
                name = self.unaccent(p.get(sec_p, 'Denumire'))
                Categorie = p.get(sec_p, 'Categorie')

                if Categorie not in categorii:
                    categ = self.env["product.category"].search([('name', '=', Categorie)], limit=1)
                    if not categ:
                        categ = self.env["product.category"].create({'name': Categorie})
                    categorii[Categorie] = categ
                else:
                    categ = categorii[Categorie]

                CotaTVA = p.get(sec_p, 'CotaTVA')

                if CotaTVA not in tax:
                    sale_tax = self.env['account.tax'].search([('type_tax_use', '=', 'sale'),
                                                               ('amount', '=', CotaTVA)], limit=1)
                    purchase_tax = self.env['account.tax'].search([('type_tax_use', '=', 'purchase'),
                                                                   ('amount', '=', CotaTVA)], limit=1)
                    tax[CotaTVA] = {'sale_tax': sale_tax, 'purchase_tax': purchase_tax}

                else:
                    sale_tax = tax[CotaTVA]['sale_tax']
                    purchase_tax = tax[CotaTVA]['purchase_tax']

                product = self.env['product.product'].create({
                    'name': name,
                    'default_code': CodProdus,
                    'categ_id': categ.id,
                    'taxes_id': [(6, False, sale_tax.ids)],
                    'supplier_taxes_id': [(6, False, purchase_tax.ids)]
                })
            bom = self.env['mrp.bom']._bom_find(product=product)

            if not bom:
                bom = self.env['mrp.bom'].create({
                    'type': 'normal',
                    'product_tmpl_id': product.product_tmpl_id.id,
                    'product_id': product.id
                })
                for i in range(1, TotalMaterii + 1):
                    item = p.get(sec_i, 'Item_%s' % i).split(';')

                    cod = item[0]
                    cant = float(item[1])
                    if cant == 0.0:
                        cant = 0.001
                    if cod not in coponente:
                        comp = self.import_un_articol(cod)
                        coponente[cod] = comp
                    else:
                        comp = coponente[cod]

                    self.env['mrp.bom.line'].create({
                        'bom_id': bom.id,
                        'product_id': comp.id,
                        'product_uom_id': comp.uom_id.id,
                        'product_qty': cant
                    })
                self.env.cr.commit()
        return

    def import_un_articol(self, cod, um=None):
        product = self.env['product.product'].search([('default_code', '=', cod)], limit=1)
        if not product:
            data = self.zip_archive.open('Articole.txt')
            p = ConfigParser.ConfigParser()
            p.readfp(data)
            product = self.import_un_articol_conf(p, cod, um)
        return product

    def import_un_articol_conf(self, p, cod, um=None):
        sec = 'ArticoleNoi_%s' % cod
        name = self.unaccent(p.get(sec, 'Denumire'))
        if um:
            uom = self.env['uom.uom'].search([('name', '=', um)], limit=1)
            if not uom:
                uom_id = self.env['uom.uom'].name_create(um)[0]
            else:
                uom_id = uom.id
        values = {
            'name': name,
            'default_code': cod
        }
        if um:
            values['uom_id'] = uom_id
            values['uom_po_id'] = uom_id

        product = self.env['product.product'].create(values)
        self.env.cr.commit()
        return product

    def import_articole(self, data):
        """
        [ArticoleNoi_cod]
        Denumire=Descriere
        Serviciu=N
        ContServiciu=
        """
        p = ConfigParser.ConfigParser()
        p.readfp(data)
        for sec in p.sections():
            cod = sec.replace('ArticoleNoi_', '')
            product = self.env['product.product'].search([('default_code', '=', cod)], limit=1)
            if not product:
                self.import_un_articol_conf(p, cod)

    def import_un_partener(self, cod):
        partner = self.env['res.partner'].search([('ref', '=', cod)], limit=1)
        if not partner:
            data = self.zip_archive.open('Partner.txt')
            p = ConfigParser.ConfigParser()
            p.readfp(data)
            partner = self.import_un_partener_conf(p, cod)
        return partner

    def import_un_partener_conf(self, p, cod):
        sec = 'ParteneriNoi_%s' % cod
        name = self.unaccent(p.get(sec, 'Denumire'))
        city = self.unaccent(p.get(sec, 'Localitate'))
        street = self.unaccent(p.get(sec, 'Adresa'))
        CodFiscal = p.get(sec, 'CodFiscal')

        country = self.env.user.company_id.country_id
        vat = CodFiscal
        cnp = ''
        is_company = True

        if vat:
            vat = ''.join(x for x in vat if x.isdigit())

        if vat:
            if len(vat) == 13:
                cnp = vat
                vat = ''
                is_company = False
            else:
                vat = country.code + vat

        values = {
            'name': name,
            'ref': cod,
            'city': city,
            'is_company': is_company,
            'street': street,
        }
        partner = self.env['res.partner'].create(values)
        if vat or cnp:
            try:
                partner.write({'vat': vat, 'cnp': cnp})
            except Exception as e:
                pass

        self.env.cr.commit()
        return partner

    def import_parteneri(self, data):
        """
        [ParteneriNoi_33044]
        Denumire=
        Localitate=
        Adresa=STR TRANTOMIR NR 12 A BIROU 1 IN SPATE LA PIZZERIA DOMNEASCA
        Sediu=
        RegistruComert=
        MarcaAgent=
        Clasa=
        CodFiscal=
        Judet=
        """
        p = ConfigParser.ConfigParser()
        p.readfp(data)
        for sec in p.sections():
            cod = sec.replace('ParteneriNoi_', '')
            partner = self.env['res.partner'].search([('ref', '=', cod)], limit=1)
            if not partner:
                self.import_un_partener_conf(p, cod)

    def import_nir(self, data):
        """
        [InfoPachet]
        AnLucru=2017
        LunaLucru=08
        TipDocument=FACTURA INTRARE
        TotalFacturi=403

        [Factura_1]
        NrDoc=477152
        Data=18.08.2017
        CodFurnizor=81
        TVAINCASARE=false
        Scadenta=22.08.2017
        Majorari=0
        TotalArticole=13
        Discount=0.0
        [Items_1]
        Item_1=M1052;ST.;24.0;25.21;BAR;0.0;;60.0;
        Item_2=M526;ST.;6.0;20.0;BAR;0.0;;55.0;
        Item_3=M1241;ST.;6.0;33.5;BAR;0.0;;85.0;
        Item_4=M866;ST.;6.0;12.1;BAR;0.0;;40.0;
        Item_5=M868;ST.;6.0;24.0;BAR;0.0;;60.0;
        """
        p = ConfigParser.ConfigParser()
        p.readfp(data)
        item_count = int(p.get('InfoPachet', 'TotalFacturi'))
        tax = {}
        coponente = {}
        categorii = {}
        for nr in range(1, item_count + 1):
            sec_p = 'Factura_%s' % nr
            sec_i = 'Items_%s' % nr
            CodFurnizor = p.get(sec_p, 'CodFurnizor')

            partner = self.import_un_partener(CodFurnizor)
            reference = p.get(sec_p, 'NrDoc')
            invoice = self.env['account.invoice'].search([('partner_id', '=', partner.id),
                                                          ('reference', '=', reference)], limit=1)
            if invoice:
                continue
            TotalArticole = int(p.get(sec_p, 'TotalArticole'))
            invoice_data = p.get(sec_p, 'Data')  # dd.mm.yyyy
            invoice_data = "%s-%s-%s" % (invoice_data[6:10], invoice_data[3:5], invoice_data[:2])

            date_due = p.get(sec_p, 'Scadenta')  # dd.mm.yyyy
            date_due = "%s-%s-%s" % (date_due[6:10], date_due[3:5], date_due[:2])
            invoice = self.env['account.invoice'].create({
                'partner_id': partner.id,
                'type': 'in_invoice',
                'date': invoice_data,
                'date_invoice': invoice_data,
                'date_due': date_due,
                'reference': reference
            })
            fpos = invoice.fiscal_position_id
            for i in range(1, TotalArticole + 1):
                item = p.get(sec_i, 'Item_%s' % i).split(';')
                product = self.import_un_articol(item[0], item[1])
                cant = float(item[2])
                pret = float(item[3])
                list_price = float(item[7])
                account = product.product_tmpl_id.get_product_accounts(fpos)['expense']

                taxes = product.supplier_taxes_id or account.tax_ids
                company_id = self.env.user.company_id
                taxes = taxes.filtered(lambda r: r.company_id == company_id)

                taxes = invoice.fiscal_position_id.map_tax(taxes, product, invoice.partner_id)
                values = {
                    'invoice_id': invoice.id,
                    'product_id': product.id,
                    'name': product.name,
                    'uom_id': product.uom_id.id,
                    'quantity': cant,
                    'price_unit': pret,
                    'account_id': account.id,
                    'invoice_line_tax_ids': [(6, False, taxes.ids)]
                }
                self.env["account.invoice.line"].create(values)
                product.write({'list_price': list_price})
            invoice.compute_taxes()
            self.env.cr.commit()
