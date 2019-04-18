# -*- coding: utf-8 -*-
# ©  2008-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
from odoo.exceptions import UserError
import odoo.addons.decimal_precision as dp


# todo: de facut legatura cu listele de preturi


class ProductPriceChange(models.Model):
    _name = 'product.price.change'
    _description = "Product Price Change"
    _inherit = ['mail.thread']
    _order = 'date desc'

    def _get_price_change(self, cr, uid, ids, context=None):
        result = {}
        for line in self.pool.get('product.price.change.line').browse(cr, uid, ids, context=context):
            result[line.price_change_id.id] = True
        return result.keys()

    name = fields.Char("Number", size=64, index=True, readonly=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('price.change'))

    date = fields.Date('Date', required=True, index=True, states={'done': [('readonly', True)]},
                       default=fields.Date.today)

    partner_id = fields.Many2one(related='warehouse_id.partner_id', string="Owner Address", readonly=True)

    state = fields.Selection([('draft', 'Draft'), ('done', 'Done')], 'Status', default='draft')

    line_ids = fields.One2many('product.price.change.line', 'price_change_id', 'Price History Lines',
                               states={'done': [('readonly', True)]})

    warehouse_id = fields.Many2one('stock.warehouse', 'Warehouse', states={'done': [('readonly', True)]})
    location_id = fields.Many2one('stock.location', 'Location', states={'done': [('readonly', True)]})
    company_id = fields.Many2one(
        'res.company', 'Company', required=True, index=True,
        states={'done': [('readonly', True)]},
        default=lambda self: self.env['res.company']._company_default_get('product.price.change')
    )

    # lot_stock_id = fields.related('warehouse_id', 'lot_stock_id', type="many2one", relation="stock.location", readonly=True ),
    # address_id = fields.related('lot_stock_id', 'partner_id', type="many2one", relation="res.partner", string="Address",readonly=True )

    parent_id = fields.Many2one('product.price.change', 'Parent Product Price Change', index=True, ondelete='cascade')
    child_ids = fields.One2many('product.price.change', 'parent_id', string='Child Product Price Change', readonly=True)

    old_amount = fields.Monetary(compute="_compute_amount_all", digits=dp.get_precision('Account'), string='Old Amount')
    new_amount = fields.Monetary(compute="_compute_amount_all", digits=dp.get_precision('Account'), string='New Amount')
    diff_amount = fields.Monetary(compute="_compute_amount_all", digits=dp.get_precision('Account'),
                                  string='Difference Amount')

    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

    @api.multi
    @api.depends('line_ids.old_price', 'line_ids.new_price', 'line_ids.quantity')
    def _compute_amount_all(self):
        for change in self:

            old_amount = 0
            new_amount = 0

            for line in change.line_ids:
                old_amount += line.old_price * line.quantity
                new_amount += line.new_price * line.quantity

            change.old_amount = old_amount
            change.new_amount = new_amount
            change.diff_amount = new_amount - old_amount

    @api.multi
    def action_confirm(self):
        self.write({'state': 'done'})
        # aici se actualizeaza si preturile din produse

        for change in self:
            if not change.location_id:
                locations = self.env['stock.location'].search([('usage', '=', 'internal')])

                for location in locations:
                    new_lines = []
                    warehouse = location.get_warehouse()
                    for line in change.line_ids:

                        available = 0
                        quant_ids = self.env['stock.quant'].search([('product_id', '=', line.product_id.id),
                                                                    ('location_id', '=', location.id)])

                        for quant in quant_ids:
                            available += quant.quantity
                        # available = line.product_id.qty_available

                        if available != 0:
                            new_lines.append([0, 0, {'product_id': line.product_id.id,
                                                     'old_price': line.old_price,
                                                     'new_price': line.new_price,
                                                     'quantity': available,
                                                     }])

                    if len(new_lines) > 0:
                        change_id = self.create({
                            'name': change.name,
                            'parent_id': change.id,
                            'warehouse_id': warehouse.id,
                            'location_id': location.id,
                            'state': 'done',
                            'line_ids': new_lines})
                        if warehouse.partner_id:
                            self.message_subscribe([warehouse.partner_id.id])
                        self.message_post(body=_('New Price Change'), type='comment',
                                          subtype='mail.mt_comment')

            for change in self:
                for line in change.line_ids:
                    line.product_id.with_context(ref=change.name).write({'list_price': line.new_price})

        return True

    @api.multi
    def unlink(self):
        for change in self:
            if change.state not in ['draft']:
                raise UserError(_("Change Price document with status 'Done' cant't by deleted"))
        return super(ProductPriceChange, self).unlink()

    @api.onchange('warehouse_id')
    def onchange_warehouse_id(self):
        if self.warehouse_id:
            self.partner_id = self.warehouse_id.partner_id.id


class ProductPriceChangeLine(models.Model):
    _name = 'product.price.change.line'
    _rec_name = 'product_id'

    price_change_id = fields.Many2one('product.price.change', 'Product Price Change', readonly=True)
    sequence = fields.Integer('Sequence',
                              help="Gives the sequence order when displaying a list of product with price changed.")
    product_id = fields.Many2one('product.product', 'Product', required=True)

    old_price = fields.Float('Old Sale Price', compute='_compute_old_amount', digits=dp.get_precision('Sale Price'),
                             readonly=True, store=True)
    old_amount = fields.Monetary(compute='_compute_old_amount', string='Old Amount', digits=dp.get_precision('Account'),
                                 readonly=True, store=True)

    new_price = fields.Float('New Sale Price', required=True, digits=dp.get_precision('Sale Price'))
    new_amount = fields.Monetary(compute='_compute_new_amount', string='New Amount', digits=dp.get_precision('Account'),
                                 readonly=True, store=True)

    diff_amount = fields.Monetary(compute='_compute_diff_amount', string='Difference Amount',
                                  digits=dp.get_precision('Account'), readonly=True, store=True)

    quantity = fields.Float('Quantity', digits=dp.get_precision('Product Unit of Measure'), readonly=True,
                            compute='_compute_quantity', store=True)

    currency_id = fields.Many2one('res.currency', related='price_change_id.currency_id')

    @api.multi
    @api.depends('old_price', 'quantity')
    def _compute_old_amount(self):
        for line in self:
            line.old_amount = line.old_price * line.quantity

    @api.multi
    @api.depends('new_price', 'quantity')
    def _compute_new_amount(self):
        for line in self:
            line.new_amount = line.new_price * line.quantity

    @api.multi
    @api.depends('old_price', 'new_price', 'quantity')
    def _compute_diff_amount(self):
        for line in self:
            line.diff_amount = line.new_price * line.quantity - line.old_price * line.quantity

    @api.multi
    @api.depends('product_id')
    def _compute_quantity(self):
        for line in self:
            line.quantity = line.product_id.with_context(warehouse=line.price_change_id.warehouse_id.id,
                                                         location=line.price_change_id.location_id.id).qty_available
            line.old_price = line.product_id.list_price

    @api.onchange('product_id')
    def onchange_product_id(self):

        def get_child(location_ids, location):
            for child in location.child_ids:
                location_ids.append(child.id)
                get_child(location_ids, child)
            return location_ids

        if not self.product_id:
            return {}

        product = self.product_id
        # available = 0
        # if self.price_change_id.warehouse_id:
        #     available = 0
        #     warehouse = self.price_change_id.warehouse_id
        #     location_ids = [warehouse.lot_stock_id.id]
        #     location = warehouse.lot_stock_id
        #     get_child(location_ids, location)
        #
        #     quant_ids = self.env['stock.quant'].search([('product_id', '=', product.id),
        #                                                 ('location_id', 'in', location_ids)])
        #     for quant in quant_ids:
        #         available = available + quant.quantity
        # else:
        #     available = product.qty_available  # self.pool.get('product.product').get_product_available(cr, uid,  [prod_id], c)[prod_id]

        self.old_price = product.list_price
        # self.quantity = available
        self.new_price = product.list_price
