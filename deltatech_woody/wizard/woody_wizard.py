# -*- coding: utf-8 -*-

import base64

import bc
from odoo import models, fields, api, _
from odoo.exceptions import Warning

try:
    import xlrd

    try:
        from xlrd import xlsx
    except ImportError:
        xlsx = None
except ImportError:
    xlrd = xlsx = None


class woody_wizard(models.TransientModel):
    _name = 'woody.wizard'
    _description = "Woody Wizard"

    file_bc = fields.Binary(string="File BOM")
    filename_bc = fields.Char('File Name BOM', required=True)
    without_half_product = fields.Boolean(string="Without Half Product")
    file_dc = fields.Binary(string="File Chart of Debiting")
    filename_dc = fields.Char('File Name Chart of Debiting', required=True)

    product_tmpl_id = fields.Many2one('product.template', 'Product',
                                      domain="[('type', 'in', ['product', 'consu'])]", required=True)
    product_id = fields.Many2one('product.product', 'Product Variant',
                                 domain="['&', ('product_tmpl_id', '=', product_tmpl_id), ('type', 'in', ['product', 'consu'])]")

    @api.model
    def default_get(self, fields):
        defaults = super(woody_wizard, self).default_get(fields)

        active_id = self.env.context.get('active_id', False)
        model = self.env.context.get('active_model', False)

        if model == 'product.template':
            product_tmpl = self.env['product.template'].browse(active_id)
            if product_tmpl:
                defaults['product_tmpl_id'] = product_tmpl.id
        if model == 'product.product':
            product = self.env['product.product'].browse(active_id)
            if product:
                defaults['product_id'] = product.id
                defaults['product_tmpl_id'] = product.product_tmpl_id.id

        return defaults

    @api.multi
    def do_import(self):

        attribute_value = self.env['product.attribute.value']
        route_manufacture = self.env.ref('mrp.route_warehouse0_manufacture')
        uom_unit = self.env.ref('product.product_uom_unit')
        uom_square_meter = self.env.ref('product.product_uom_square_meter')
        uom_meter = self.env.ref('product.product_uom_meter')
        category_blat = self.env.ref('product.product_category_blat')


        with_attr = False
        attr_set = ('dimension', 'color', 'height', 'texture', 'cant')  # de renuntat la atributele de dimensiune

        attribute = {}

        for att in attr_set:
            attribute[att] = self.env.ref('product.product_attribute_' + att)
            if not attribute['dimension']:
                raise Warning(_('Nu gasesc atributul %s'), att)

        file_bc = base64.b64decode(self.file_bc)
        file_dc = base64.b64decode(self.file_dc)

        woody_data = bc.extract(file_bc, file_dc)

        bom = self.env['mrp.bom'].create({
            'type': 'normal', 'product_tmpl_id': self.product_tmpl_id.id, 'product_id': self.product_id.id,
        })

        self.product_tmpl_id.write({'name': woody_data['name'],
                                    'sale_ok': True,
                                    'purchase_ok': False,
                                    'type': 'product',
                                    'route_ids': [(6, False, [route_manufacture.id])],
                                    'categ_id': self.env.ref('product.product_category_finish').id})

        finish_product_code = self.product_id.default_code or self.product_tmpl_id.default_code

        if not finish_product_code:
            finish_product_code = self.env['ir.sequence'].next_by_code('product.sequence_finish_product')
            self.product_tmpl_id.write({'default_code': finish_product_code})

        # adaugare produse auxiliare
        category_aux = self.env.ref('product.product_category_aux')
        for prod in woody_data['products']['Aux']:
            self.get_product(prod, category_aux)

        # adaugare produse canturi
        category_raw = self.env.ref('product.product_category_strip')
        for prod in woody_data['products']['Canturi']:
            self.get_product(prod, category_raw)

        # materie prima placi
        category_raw = self.env.ref('product.product_category_raw')
        for prod in woody_data['products']['Placi']:
            self.get_product(prod, category_raw, placi=True)

        half = 1
        i = 10


        for cod, v in woody_data['pachete'].iteritems():
            for item in v:

                routing_code = item['routing']

                routing_id = self.env['mrp.routing'].search([('name', '=', routing_code)], limit=1)
                if not routing_id:
                    routing_id = self.env['mrp.routing'].create({'name': routing_code})

                # determinare materie prima pentru semifabricate
                if item['raw_product'] in woody_data['echivalente']:
                    raw_code = woody_data['echivalente'][item['raw_product']]
                    raw_product = self.env['product.product'].search([('default_code', '=', raw_code)], limit=1)
                else:
                    raise Warning(_('Nu gasesc materia prima pentru codul %s') % raw_code)

                """
                if raw_product.categ_id == category_blat: # daca este vorba de un blat
                    continue
                """

                # poate e mai bine ca sa fac codificarea in functie de codul produsului finit la care sa adaug
                # v_code = raw_code + ' ' + routing_code + v_size
                # v_code = finish_product_code + '-' + item['code']
                if not self.without_half_product:
                    v_code = finish_product_code + '/' + str(half).zfill(2)
                    half += 1

                    if with_attr:
                        att_val = {}
                        for att in attr_set:
                            att_val[att] = attribute_value.search([('name', '=', item[att]),
                                                                   ('attribute_id', '=', attribute[att].id)], limit=1)
                            if not att_val[att]:
                                att_val[att] = attribute_value.create({'name': item[att],
                                                                       'attribute_id': attribute[att].id})
                    value = {'name': '%s' % (item['code']),
                             'type': 'product',
                             'uom_id': uom_unit.id,
                             'default_code': v_code,
                             'sale_ok': False,
                             'purchase_ok': False,
                             'attribute_line_ids': [],
                             'length': item['x'],
                             'width': item['y'],
                             'height': item['height'],
                             'categ_id': self.env.ref('product.product_category_half').id,
                             'route_ids': [(6, False, [route_manufacture.id])]}

                    if with_attr:
                        for att in attr_set:
                            value['attribute_line_ids'] += [(0, 0, {'attribute_id': attribute[att].id})]

                    product = self.env['product.product'].create(value)
                    if with_attr:
                        for line in product.attribute_line_ids:
                            for att in attr_set:
                                if line.attribute_id == attribute[att]:
                                    line.write({'value_ids': [(4, att_val[att].id, False)]})

                        for att in attr_set:
                            att_val[att].write({'product_ids': [(4, product.id, False)]})

                    self.env['mrp.bom.line'].create({
                        'sequence': i,
                        'bom_id': bom.id,
                        'product_id': product.id,
                        'product_uom_id': product.uom_id.id,
                        'product_qty': item['qty']
                    })

                    i += 10

                    sub_bom = self.env['mrp.bom'].create({
                        'type': 'normal',
                        'product_tmpl_id': product.product_tmpl_id.id,
                        'product_id': product.id,
                        'routing_id': routing_id.id
                    })
                else:
                    sub_bom = bom

                v_row_cant = float(item['x']) * float(item['y']) / (1000.0 * 1000.0)

                if raw_product.categ_id != category_blat:
                    uom = self.env['product.uom'].search([('name', '=', item['dimension']),
                                                          ('category_id', '=', uom_square_meter.category_id.id)], limit=1)
                    if not uom:
                        uom = self.env['product.uom'].create({'name': item['dimension'],
                                                              'category_id': uom_square_meter.category_id.id,
                                                              'uom_type': 'bigger', 'factor': 1 / v_row_cant})
                else:
                    uom_text = '%s mm' % item['x']
                    v_row_cant = float(item['x']) / 1000.0
                    uom = self.env['product.uom'].search([('name', '=', uom_text),
                                                          ('category_id', '=', uom_meter.category_id.id)], limit=1)
                    if not uom:
                        uom = self.env['product.uom'].create({'name': uom_text,
                                                              'category_id': uom_meter.category_id.id,
                                                              'uom_type': 'bigger', 'factor': 1 / v_row_cant})
                bom_line = {'bom_id': sub_bom.id,
                            'product_id': raw_product.id,
                            'product_uom_id': uom.id,
                            'product_qty': 1}

                if item['texture'].lower() == 'da':
                    bom_line['item_categ'] = 'cut_fiber'
                else:
                    bom_line['item_categ'] = 'cut'

                self.env['mrp.bom.line'].create(bom_line)

                cant_ord = ('right', 'left', 'top', 'bottom')
                # adaugare canturi
                if item['canturi'] and item['canturi'][1]:
                    cant_poz = 0
                    for cant in item['canturi'][1]:
                        if cant:
                            cant_code = woody_data['echivalente'][cant[1]]
                            cant_product = self.env['product.product'].search([('default_code', '=', cant_code)])
                            if not cant_product:
                                raise Warning(_('Nu gasesc materia prima pentru codul %s') % cant_code)

                            if cant_poz == 0 or cant_poz == 1:
                                v_cant_qty = float(item['y']) + 100.0  # la care se mai aduaga 10 cm
                            else:
                                v_cant_qty = float(item['x']) + 100.0  # la care se mai aduaga 10 cm

                            v_cant_qty = v_cant_qty / 1000.0  # transformare cant in metri
                            item_categ = cant_ord[cant_poz]

                            self.env['mrp.bom.line'].create({
                                'bom_id': sub_bom.id,
                                'item_categ': item_categ,
                                'product_id': cant_product.id,
                                'product_uom_id': cant_product.uom_id.id,
                                'product_qty': v_cant_qty
                            })
                        cant_poz += 1


        # adaugare produse auxiliare
        for prod in woody_data['products']['Aux']:
            # prod = self.get_product(prod, self.env.ref('product.product_category_aux'))

            self.env['mrp.bom.line'].create({
                'sequence': i,
                'bom_id': bom.id,
                'product_id': prod['product_id'].id,
                'product_uom_id': prod['uom_id'].id,
                'product_qty': prod['qty']
            })
            i += 10

    @api.model
    def get_product(self, item, categ_id,  placi=False):
        # v_name, v_code, v_uom, v_cant, v_price, v_amount = item
        bom_uom = False
        uom = False
        price = item['price']

        if 'profil' in item and item['profil']:
            categ_id = self.env.ref('product.product_category_profile')
            uom_categ_length = self.env.ref('product.uom_categ_length')
            bom_uom = self.env['product.uom'].search([('name', '=', item['uom']),
                                                      ('category_id', '=', uom_categ_length.id)], limit=1)
            dim = float(item['uom'].replace(" mm", ''))
            if not bom_uom:
                factor = 1000.0 / dim
                bom_uom = self.env['product.uom'].create({'name': item['uom'],
                                                          'category_id': uom_categ_length.id,
                                                          'uom_type': 'smaller',
                                                          'factor': factor})
            price = 1000 * float(item['price']) / dim
            uom = self.env.ref('product.product_uom_meter')  # ('product.product_uom_mm') # stocul se tine totusi in mm

        if item['uom'] == 'buc' or item['uom'] == 'buc.':
            uom = self.env.ref('product.product_uom_unit')

        if item['uom'] == 'metru patrat' or item['uom'] == 'm2' or item['uom'] == 'mp':
            uom = self.env.ref('product.product_uom_square_meter')

        if item['uom'] == 'rm' or item['uom'] == 'm':
            uom = self.env.ref('product.product_uom_meter')
            if placi:  # placile masurate in m sunt de fapt baturi
                categ_id = self.env.ref('product.product_category_blat')


        if not uom:
            uom = self.env['product.uom'].search([('name', '=', item['uom'])], limit=1)
        if not uom:
            raise Warning(_('Please create UOM %s') % item['uom'])

        product = self.env['product.product'].search([('default_code', '=', item['code'])], limit=1)
        if not product:
            route_warehouse0_buy = self.env.ref('purchase.route_warehouse0_buy')

            vals = {
                'name': item['name'].replace('_', ' '),
                'type': 'product',
                'default_code': item['code'],
                'list_price': price,
                'standard_price': price,
                'uom_id': uom.id,
                'uom_po_id': uom.id,
                'sale_ok': False,
                'purchase_ok': True,
                'route_ids': [(6, False, [route_warehouse0_buy.id])],
                'categ_id': categ_id.id
            }
            if 'profil' in item and item['profil']:
                vals['categ_id'] = self.env.ref('product.product_category_profile').id

            product = self.env['product.product'].create(vals)
        if product.uom_id.category_id != uom.category_id:
            raise Warning(_('Unit %s can not be used for product %s') % (uom.name, product.name))
        item['product_id'] = product
        if bom_uom:
            item['uom_id'] = bom_uom
        else:
            item['uom_id'] = uom
        return item
