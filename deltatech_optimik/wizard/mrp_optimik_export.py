# coding=utf-8


from odoo import models, fields, api
import csv
from cStringIO import StringIO
import base64


class MrpOptimikExport(models.TransientModel):
    _name = 'mrp.optimik.export'
    _description = "MRP Optimik Export"

    name = fields.Char()
    date = fields.Date()
    description = fields.Char()
    file_type = fields.Selection([('csv','csv'),('txt','txt')], default='txt')
    state = fields.Selection([('choose', 'choose'),  # choose product
                              ('prepare', 'Prepare'),
                              ('get_file', 'Get File')], default='choose')  # get the file

    separator = fields.Char(default='|', size=1)
    no_labels = fields.Boolean(string="Without Label", default=True)

    line_ids = fields.One2many("mrp.optimik.select.line", 'optimik_id', string='Select lines')
    line_export_ids = fields.One2many("mrp.optimik.export.line", 'optimik_id', string='Export lines')

    file_name = fields.Char(string='File Name', default="Optimik.txt", compute="_compute_file_name")
    data_file = fields.Binary(string='File', readonly=True)

    @api.depends('file_type')
    def _compute_file_name(self):
        self.file_name = 'Optimik_%s_.%s' % ( fields.Date.today(), self.file_type)

    @api.model
    def default_get(self, fields):
        res = super(MrpOptimikExport, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        model = self.env.context.get('active_model', False)

        uom_categ_surface = self.env.ref('product.uom_categ_surface')
        line_ids = []
        product_list = {}
        products = self.env['product.product']

        raw_product = False
        lines = self.env["mrp.optimik.select.line"]

        if model == 'mrp.production':
            productions = self.env['mrp.production'].browse(active_ids)
            for production in productions:
                line = False
                moves = production.move_raw_ids.sorted(key=lambda r: r.bom_line_id.sequence)
                for move in moves:
                    if move.bom_line_id.item_categ in ['cut', 'cut_fiber']:
                        raw_product = move.product_id
                        if ' x ' in move.product_uom.name:
                            length, width = move.product_uom.name.split('x')
                            values = {
                                'product_id': production.product_id.id,
                                'raw_product': raw_product.id,
                                'quantity': move.product_uom_qty,
                                'uom_id': move.product_uom.id,
                                'length': length,
                                'width': width,
                                'fiber': (move.bom_line_id.item_categ == 'cut_fiber'),
                                'description': move.bom_line_id.name,
                                'set': production.procurement_group_id.name
                            }
                            if move.bom_line_id.name == raw_product.name:
                                values['description'] = production.product_id.name

                            line = self.env["mrp.optimik.select.line"].create(values)
                            lines |= line
                    # sper ca liniile sa fie in ordinea din BOM !!!!???
                    if line:
                        if move.bom_line_id.item_categ == 'top':
                            line.write({'strip_top': move.product_id.id})
                        if move.bom_line_id.item_categ == 'left':
                            line.write({'strip_left': move.product_id.id})
                        if move.bom_line_id.item_categ == 'right':
                            line.write({'strip_right': move.product_id.id})
                        if move.bom_line_id.item_categ == 'bottom':
                            line.write({'strip_bottom': move.product_id.id})

        if lines:
            line_ids.append([6, 0, lines.ids])

        """
        if model == 'product.template':
            product_tmpl = self.env['product.template'].browse(active_ids)
            for tmpl in product_tmpl:
                products |= tmpl.product_variant_ids

        if model == 'product.product':
            products = self.env['product.product'].browse(active_ids)

        for product in products:
            product_list[product.id] = {'product_id': product.id, 'quantity': 1}

        # are sens pt o comanda de vanzare ?
        if model == 'sale.order':
            sale_orders = self.env['sale.order'].browse(active_ids)
            for sale_order in sale_orders:
                for line in sale_order.order_line:

                        products |= line.product_id
                        if line.product_id.id not in product_list:
                            product_list[line.product_id.id] = {'product_id': line.product_id.id,
                                                                'quantity': line.product_uom_qty}
                        else:
                            product_list[line.product_id.id]['quantity'] += line.product_uom_qty
         
        if model == 'mrp.production':
            productions = self.env['mrp.production'].browse(active_ids)
            for production in productions:
                for move in production.move_raw_ids:
                    products |= move.product_id
                    if move.product_id.id not in product_list:
                        product_list[move.product_id.id] = {'product_id': move.product_id.id,
                                                            'quantity': move.product_uom_qty}
                    else:
                        product_list[move.product_id.id]['quantity'] += move.product_uom_qty
        
        for product in products:

                values = product_list[product.id]
                values['length'] = product.length
                values['width'] = product.width
                bom = self.env['mrp.bom']._bom_find(product=product)
                if bom:
                    for line in bom.bom_line_ids:
                        if line.item_categ in ['cut', 'cut_fiber']:
                            values['is_ok'] = True  # Am gasit ceva de taiat!
                            values['raw_product'] = line.product_id.id
                            if line.item_categ == 'cut_fiber':
                                values['fiber'] = True
                        if line.item_categ == 'top':
                            values['strip_top'] = line.product_id.id
                        if line.item_categ == 'left':
                            values['strip_left'] = line.product_id.id
                        if line.item_categ == 'right':
                            values['strip_right'] = line.product_id.id
                        if line.item_categ == 'bottom':
                            values['strip_bottom'] = line.product_id.id

                line_ids.append([0, 0, values])
        """
        res['line_ids'] = line_ids

        return res

    @api.multi
    def do_export(self):

        if self.no_labels:
            lines = self.env['mrp.optimik.select.line'].read_group(
                domain=[('optimik_id', '=', self.id)],
                fields=['raw_product', 'fiber', 'description', 'set', 'length', 'width', 'quantity'],
                groupby=['raw_product', 'fiber',  'length', 'width'], lazy=False)
        else:
            lines = self.env['mrp.optimik.select.line'].read_group(
                domain=[('optimik_id', '=', self.id)],
                fields=['raw_product', 'fiber', 'description', 'set', 'length', 'width', 'quantity',
                        'strip_top', 'strip_left', 'strip_right', 'strip_bottom'],
                groupby=['raw_product', 'fiber', 'description', 'set', 'length', 'width',
                         'strip_top', 'strip_left', 'strip_right', 'strip_bottom'], lazy=False)

        for line in lines:
            vals = {
                'optimik_id': self.id,
                'raw_product': line['raw_product'][0],
                'quantity': line['quantity'],
                'length': line['length'],
                'width': line['width'],
                'fiber': line['fiber'],
                'description': '',
                'set':''
            }
            if not self.no_labels:
                vals['strip_top'] = line['strip_top'] and line['strip_top'][0]
                vals['strip_left'] = line['strip_left'] and line['strip_left'][0]
                vals['strip_right'] = line['strip_right'] and line['strip_right'][0]
                vals['strip_bottom'] = line['strip_bottom'] and line['strip_bottom'][0]
                vals['description'] = line['description'] or ''
                vals['set'] = line['set'] or ''

            self.env["mrp.optimik.export.line"].create(vals)

        self.write({'state': 'prepare'})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.optimik.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    @api.multi
    def do_make_file(self):
        fp = StringIO()
        writer = csv.writer(fp, quoting=csv.QUOTE_NONE, delimiter=self.separator.encode('ascii', 'ignore'))

        # D | cod material | nr buc | lungime | latime. | Fibra | nume piesa | Client | cant fata | Cant stanga | cant spate | cant dreapta


        fields = ['D', 'cod material', 'nr buc', 'lungime', 'latime', 'Fibra',
                  'nume piesa', 'client', 'cant fata', 'cant stanga', 'cant spate', 'cant dreapta']

        # writer.writerow([name.encode('utf-8') for name in fields])

        for line in self.line_export_ids:
            row = []
            row.append('D')
            row.append(line.raw_product.default_code)
            row.append(line.quantity)

            row.append(line.length)
            row.append(line.width)

            if line.fiber:
                row.append('=')
            else:
                row.append('X')

            row.append(line.description)  # nume piesa
            row.append(line.set)  # client
            if self.no_labels:
                row.append('')  # cant fata
                row.append('')  # cant stanga
                row.append('')  # cant spate
                row.append('')  # cant dreapta
            else:
                row.append(line.strip_top.name or '')  # cant fata
                row.append(line.strip_left.name or '')  # cant stanga
                row.append(line.strip_bottom.name or '')  # cant spate
                row.append(line.strip_right.name or '')  # cant dreapta

            writer.writerow(row)

        fp.seek(0)
        data_file = base64.encodestring(fp.read())
        fp.close()

        self.write({'state': 'get_file',
                    'data_file': data_file})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.optimik.export',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }


class MrpOptimikSelectLine(models.TransientModel):
    _name = "mrp.optimik.select.line"

    optimik_id = fields.Many2one('mrp.optimik.export', string="Product Label")
    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Integer(string="Qty", default=1, group_operator='sum')
    #    is_ok = fields.Boolean()

    length = fields.Float()  # related='product_id.length', readonly=True, store=True)
    width = fields.Float()  # related='product_id.width', readonly=True, store=True)

    description = fields.Char(string="Description")
    set = fields.Char(string="Set")
    raw_product = fields.Many2one('product.product')  # , compute="_compute_is_ok", store=True)
    fiber = fields.Boolean()
    strip_top = fields.Many2one('product.product')  # , compute="_compute_is_ok", store=True)
    strip_left = fields.Many2one('product.product')  # , compute="_compute_is_ok", store=True)
    strip_right = fields.Many2one('product.product')  # , compute="_compute_is_ok", store=True)
    strip_bottom = fields.Many2one('product.product')  # , compute="_compute_is_ok", store=True)
    uom_id = fields.Many2one('product.uom', 'Unit of Measure', domain="[('category_id','=', uom_categ_id)]")
    uom_categ_id = fields.Many2one('product.uom.categ', related='raw_product.uom_id.category_id')

    @api.onchange('product_id')
    def _compute_is_ok(self):
        for line in self:
            line.is_ok = False
            line.raw_product = False
            line.length = line.product_id.length
            line.width = line.product_id.width
            if line.product_id:
                bom = self.env['mrp.bom']._bom_find(product=line.product_id)
                if bom:
                    for line in bom.bom_line_ids:
                        if line.item_categ in ['cut', 'cut_fiber']:
                            line.is_ok = True  # Am gasit ceva de taiat!
                            line.raw_product = line.product_id
                            if line.item_categ == 'cut_fiber':
                                line.fiber = True
                        if line.item_categ == 'top':
                            line.strip_top = line.product_id
                        if line.item_categ == 'left':
                            line.strip_left = line.product_id
                        if line.item_categ == 'right':
                            line.strip_right = line.product_id
                        if line.item_categ == 'bottom':
                            line.strip_bottom = line.product_id


class MrpOptimikExportLine(models.TransientModel):
    _name = "mrp.optimik.export.line"

    optimik_id = fields.Many2one('mrp.optimik.export', string="Optimik")
    raw_product = fields.Many2one('product.product')

    quantity = fields.Integer(string="Qty", default=1)
    length = fields.Float()
    width = fields.Float()
    fiber = fields.Boolean()

    description = fields.Char(string="Description")
    set = fields.Char(string="Set")

    strip_top = fields.Many2one('product.product')  # , compute="_compute_is_ok", store=True)
    strip_left = fields.Many2one('product.product')  # , compute="_compute_is_ok", store=True)
    strip_right = fields.Many2one('product.product')  # , compute="_compute_is_ok", store=True)
    strip_bottom = fields.Many2one('product.product')  # , compute="_compute_is_ok", store=True)
