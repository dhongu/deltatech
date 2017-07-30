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
    file_dc = fields.Binary(string="File Chart of Debiting")
    filename_dc = fields.Char('File Name Chart of Debiting', required=True)

    product_tmpl_id = fields.Many2one(
        'product.template', 'Product',
        domain="[('type', 'in', ['product', 'consu'])]", required=True)
    product_id = fields.Many2one(
        'product.product', 'Product Variant',
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
        file_bc = base64.b64decode(self.file_bc)
        file_dc = base64.b64decode(self.file_dc)

        woody_data = bc.extract(file_bc, file_dc)

        bom = self.env['mrp.bom'].create({
            'type': 'normal',
            'product_tmpl_id': self.product_tmpl_id.id,
            'product_id': self.product_id.id,
        })
        i = 10

        if woody_data['name']:
            self.product_tmpl_id.write({'name': woody_data['name']})

        # materie prima placi
        for cod, v in woody_data['placi'].iteritems():
            for item in v:
                self.get_product(item)

        for cod, v in woody_data['pachete'].iteritems():
            for item in v:
                v_size = " (%s x %s)" % (str(item[3]), str(item[4]))
                routing_code = item[1]
                v_name = routing_code + v_size
                v_cant = item[0]
                # determinare fisa tehnolgica
                routing_id = self.env['mrp.routing'].search([('name', '=', routing_code)])
                if not routing_id:
                    # raise Warning(_('Nu este definita fisa tehnologica %s') % routing_code)
                    routing_id = self.env['mrp.routing'].create({'name': routing_code})

                # determinare materie prima pentru semifabricate
                if item[2] in woody_data['echivalente']:
                    raw_code = woody_data['echivalente'][item[2]]
                    raw_product = self.env['product.product'].search([('default_code', '=', raw_code)])
                else:
                    raise Warning(_('Nu gasesc materia prima pentru codul %s') % raw_code)

                v_code = raw_code + ' ' + routing_code + v_size

                # mai exista un semifabricat definit la fel ?
                product = self.env['product.product'].search([('default_code', '=', v_code)])

                if not product:
                    uom = self.env.ref('product.product_uom_unit')
                    attribute_dimension = self.env.ref('product.product_attribute_dimension')
                    val_size = "%s x %s" % (str(item[3]), str(item[4]))
                    att_dim_val = self.env['product.attribute.value'].search(
                        [('name', '=', val_size),
                         ('attribute_id', '=', attribute_dimension.id)])
                    if not att_dim_val:
                        att_dim_val = self.env['product.attribute.value'].create({
                            'attribute_id': attribute_dimension.id,
                            'name': val_size
                        })
                    value = {
                        'name': raw_product.name,
                        'type': 'product',
                        'uom_id': uom.id,
                        'default_code': v_code,
                        'sale_ok': False,
                        'purchase_ok': False,
                       # 'attribute_line_ids': [(0, 0, {'attribute_id': attribute_dimension.id,
                        #                               'value_ids': [(4, att_dim_val.id, False)]})],
                        # 'attribute_value_ids':(0, _, attribute_values)
                    }

                    v_code_tmpl = raw_code + ' ' + routing_code
                    product = self.env['product.product'].search([('default_code', 'like', v_code_tmpl)], limit=1)
                    if product:
                        value['product_tmpl_id'] = product.product_tmpl_id.id
                    else:
                        value['attribute_line_ids'] = [(0, 0, {'attribute_id': attribute_dimension.id})]

                    product = self.env['product.product'].create(value)
                    product.attribute_line_ids.write({'value_ids':[(4, att_dim_val.id, False)]})
                    att_dim_val.write({'product_ids': [(4, product.id, False)]})

                    new_product = True
                else:
                    new_product = False

                self.env['mrp.bom.line'].create({
                    'sequence': i,
                    'bom_id': bom.id,
                    'product_id': product.id,
                    'product_uom_id': product.uom_id.id,
                    'product_qty': v_cant
                })

                i += 10
                if new_product:
                    sub_bom = self.env['mrp.bom'].create({
                        'type': 'normal',
                        'product_tmpl_id': product.product_tmpl_id.id,
                        'product_id': product.id,
                        'routing_id': routing_id.id
                    })
                    v_row_cant = float(item[3]) * float(item[4]) / (1000 * 1000)
                    self.env['mrp.bom.line'].create({
                        'bom_id': sub_bom.id,
                        'product_id': raw_product.id,
                        'product_uom_id': raw_product.uom_id.id,
                        'product_qty': v_row_cant
                    })

        # adaugare produse
        for v in woody_data['aux']:
            product, uom = self.get_product(v)
            v_name, v_code, v_uom, v_cant, v_price, v_amount = v

            self.env['mrp.bom.line'].create({
                'sequence': i,
                'bom_id': bom.id,
                'product_id': product.id,
                'product_uom_id': uom.id,
                'product_qty': v_cant
            })
            i += 10

    @api.model
    def get_product(self, item):
        v_name, v_code, v_uom, v_cant, v_price, v_amount = item
        if v_uom == 'buc' or v_uom == 'buc.':
            uom = self.env.ref('product.product_uom_unit')
        else:
            uom = self.env['product.uom'].search([('name', '=', v_uom)])
        if not uom:
            raise Warning(_('Please create UOM %s') % v_uom)

        product = self.env['product.product'].search([('default_code', '=', v_code)])
        if not product:
            product = self.env['product.product'].create({
                'name': v_name,
                'type': 'product',
                'default_code': v_code,
                'list_price': v_price,
                'uom_id': uom.id,
                'uom_po_id': uom.id,
                'sale_ok': False,
                'purchase_ok': False,
            })
        if product.uom_id.category_id != uom.category_id:
            raise Warning(_('Unitatea de masura %s nu se poate utiliza la produsul %s') % (uom.name, product.name))
        return product, uom
