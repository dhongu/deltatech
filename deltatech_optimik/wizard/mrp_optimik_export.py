# coding=utf-8


from odoo import models, fields, api


class MrpOptimikExport(models.TransientModel):
    _name = 'mrp.optimik.export'
    _description = "MRP Optimik"

    state = fields.Selection([('choose', 'choose'),  # choose product
                              ('prepare', 'Prepare'),
                              ('get', 'get')], default='choose')  # get the file
    line_ids = fields.One2many("mrp.optimik.export.line", 'optimik_id', string='Lines')

    name = fields.Char(string='File Name', readonly=True)
    data_file = fields.Binary(string='File', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(MrpOptimikExport, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        model = self.env.context.get('active_model', False)

        line_ids = []
        product_list = {}
        products = self.env['product.product']
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
                        product_list[line.product_id.id] = {'product_id': move.product_id.id,
                                                            'quantity': move.product_uom_qty}
                    else:
                        product_list[line.product_id.id]['quantity'] += move.product_uom_qty

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

        res['line_ids'] = line_ids

        return res


class MrpOptimikExportLine(models.TransientModel):
    _name = "mrp.optimik.export.line"

    optimik_id = fields.Many2one('mrp.optimik.export', string="Product Label")
    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Integer(string="Qty", default=1)
    is_ok = fields.Boolean(compute="_compute_is_ok")

    length = fields.Float(related='product_id.length', readonly=True)
    width = fields.Float(related='product_id.width', readonly=True)

    raw_product = fields.Many2one('product.product', compute="_compute_is_ok")
    fiber = fields.Boolean()
    strip_top = fields.Many2one('product.product', compute="_compute_is_ok")
    strip_left = fields.Many2one('product.product', compute="_compute_is_ok")
    strip_right = fields.Many2one('product.product', compute="_compute_is_ok")
    strip_bottom = fields.Many2one('product.product', compute="_compute_is_ok")

    @api.depends('product_id')
    def _compute_is_ok(self):
        self.is_ok = False
        self.raw_product = False
        if self.product_id:
            bom = self.env['mrp.bom']._bom_find(product=self.product_id)
            if bom:
                for line in bom.bom_line_ids:
                    if line.item_categ in ['cut', 'cut_fiber']:
                        self.is_ok = True  # Am gasit ceva de taiat!
                        self.raw_product = line.product_id
                        if line.item_categ == 'cut_fiber':
                            self.fiber = True
                    if line.item_categ == 'top':
                        self.strip_top = line.product_id
                    if line.item_categ == 'left':
                        self.strip_left = line.product_id
                    if line.item_categ == 'right':
                        self.strip_right = line.product_id
                    if line.item_categ == 'bottom':
                        self.strip_bottom = line.product_id
