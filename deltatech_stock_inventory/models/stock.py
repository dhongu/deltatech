# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
from odoo import api
from odoo import models, fields
from odoo.exceptions import UserError
from odoo.tools.translate import _


# TODO: de adaugat pretul si in wizardul ce permite modificarea stocului


class StockInventory(models.Model):
    _inherit = 'stock.inventory'

    name = fields.Char(string='Name', default='/')
    date = fields.Datetime(string='Inventory Date', required=True, readonly=True,
                           states={'draft': [('readonly', False)]})
    note = fields.Text(string='Note')
    filterbyrack = fields.Char('Rack')

    @api.multi
    def unlink(self):
        if any(inventory.state not in ('draft', 'cancel') for inventory in self):
            raise UserError(_('You can only delete draft inventory.'))
        return super(StockInventory, self).unlink()

    @api.model
    def _get_inventory_lines(self, inventory):
        lines = super(StockInventory, self)._get_inventory_lines(inventory)
        res = []
        if inventory.filterbyrack:

            for line in lines:
                if line['product_id']:
                    product = self.env['product.product'].browse(line['product_id'])
                    if product.loc_rack and inventory.filterbyrack == product.loc_rack:
                        res.append(line)
        else:
            res = lines
        return res

    @api.multi
    def action_check(self):
        for inventory in self:
            date = inventory.date
            values = {'date': date}
            if inventory.name == '/':
                sequence = self.env.ref('deltatech_stock_inventory.sequence_inventory_doc')
                if sequence:
                    values['name'] = sequence.next_by_id()

            inventory.write(values)
            # for line in inventory.line_ids:
            #     line.write({'standard_price': line.get_price()})
        res = super(StockInventory, self).action_check()
        return res

    @api.multi
    def action_done(self, ):
        super(StockInventory, self).action_done()
        for inv in self:
            for move in inv.move_ids:
                if move.date_expected != inv.date or move.date != inv.date:
                    move.write({'date_expected': inv.date, 'date': inv.date})
        return True


class StockInventoryLine(models.Model):
    _inherit = "stock.inventory.line"
    _order = "inventory_id, location_name, categ_id, product_code, product_name, prodlot_name"

    categ_id = fields.Many2one('product.category', string="Category", related="product_id.categ_id", store=True)
    standard_price = fields.Float(string='Price')
    loc_rack = fields.Char('Rack', size=16, related="product_id.loc_rack", store=True)
    loc_row = fields.Char('Row', size=16, related="product_id.loc_row", store=True)
    loc_case = fields.Char('Case', size=16, related="product_id.loc_case", store=True)

    @api.onchange('product_id')
    def onchange_product(self):
        res = super(StockInventoryLine, self).onchange_product()
        self.standard_price = self.get_price()
        return res

    # todo: nu sunt sigur ca e bine ??? e posibil ca self sa fie gol

    @api.model
    def get_price(self):
        price = self.product_id.standard_price
        # todo: in 11 determinarea preturlui trebuie facuta din miscarile de stoc nu din quant
        # if self.product_id.cost_method == 'fifo':
        #     dom = [('company_id', '=', self.company_id.id), ('location_id', '=', self.location_id.id),
        #            ('lot_id', '=', self.prod_lot_id.id),
        #            ('product_id', '=', self.product_id.id), ('owner_id', '=', self.partner_id.id),
        #            ('package_id', '=', self.package_id.id)]
        #     dom = [('location_id', '=', self.location_id.id), ('product_id', '=', self.product_id.id),
        #            ('lot_id', '=', self.prod_lot_id.id),
        #            ('owner_id', '=', self.partner_id.id), ('package_id', '=', self.package_id.id)]
        #
        #     quants = self.env['stock.quant'].search(dom)
        #
        #     value = sum([q.inventory_value for q in quants])
        #     if self.theoretical_qty > 0:
        #         price = value / self.theoretical_qty

        return price

    """
    def onchange_createline(self, cr, uid, ids, location_id=False, product_id=False, uom_id=False, package_id=False,
                                                prod_lot_id=False, partner_id=False, company_id=False, context=None):
        res = super(stock_inventory_line,self).onchange_createline( cr, uid, ids, location_id, product_id, uom_id, package_id,
                                                                        prod_lot_id, partner_id, company_id, context)
        if product_id:
            res['value']['standard_price'] = self.get_price(cr, uid, product_id, location_id )
        return res
    """

    # TODO: de gasit noua metoda

    """
    @api.model
    def _resolve_inventory_line(self, inventory_line):

        product_qty = inventory_line.product_qty
        if inventory_line.product_id.cost_method == 'real':
            price = inventory_line.get_price()

            if not float_is_zero(abs(inventory_line.standard_price - price), precision_digits=2):
                # se completeaza o line de inventar cu cantitate zero si cu vechiul pret
                line_price = inventory_line.standard_price
                inventory_line.write({'standard_price': price, 'product_qty': 0.0})
                inventory_line.product_id.product_tmpl_id.write({'standard_price': price})
                move_id = super(StockInventoryLine, self)._resolve_inventory_line(inventory_line)

                inventory_line.write(
                    {'standard_price': line_price,
                     'product_qty': product_qty + inventory_line.theoretical_qty})

            inventory_line.product_id.product_tmpl_id.write(
                {'standard_price': inventory_line.standard_price})  # acutlizare pret in produs

        move_id = super(StockInventoryLine, self)._resolve_inventory_line(inventory_line)
        if product_qty <> inventory_line.product_qty:
            inventory_line.write({'product_qty': product_qty})
        if move_id:
            move = self.env['stock.move'].browse(move_id)
            move.action_done()

        return move_id
    """

    def _generate_moves(self):
        for inventory_line in self:
            if inventory_line.product_id.cost_method == 'fifo':
                inventory_line.product_id.write(
                    {'standard_price': inventory_line.standard_price})  # acutlizare pret in produs
        moves = super(StockInventoryLine, self)._generate_moves()
        return moves


"""
class StockHistory(models.Model):
    _inherit = 'stock.history'

    sale_value = fields.Float('Sale Value', compute='_compute_sale_value', readonly=True)

    @api.one
    def _compute_sale_value(self):
        self.sale_value = self.quantity * self.product_id.list_price

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(StockHistory, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby,
                                                   lazy=lazy)
        if 'sale_value' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    sale_value = 0.0
                    for line2 in lines:
                        sale_value += line2.sale_value
                    line['sale_value'] = sale_value
        return res


class Quant(models.Model):
    _inherit = "stock.quant"

    sale_value = fields.Float('Sale Value', compute='_compute_sale_value', readonly=True)

    @api.one
    def _compute_sale_value(self):
        self.sale_value = self.qty * self.product_id.list_price

    @api.one
    def calc_inv_value(self,vat_value,dim_value):
        #sale_value = self.qty * self.product_id.list_price
        sale_value = round((self.qty * self.product_id.list_price)/vat_value,2)
        self.inventory_value=sale_value-(sale_value*dim_value)
        self.input_amount = sale_value-(sale_value*dim_value)
        self.input_price = self.input_amount/self.qty

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        res = super(Quant, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby,
                                            lazy=lazy)
        if 'sale_value' in fields:
            for line in res:
                if '__domain' in line:
                    lines = self.search(line['__domain'])
                    sale_value = 0.0
                    for line2 in lines:
                        sale_value += line2.sale_value
                    line['sale_value'] = sale_value
        return res

"""
