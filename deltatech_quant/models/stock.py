# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
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

from odoo import models, fields, api


class stock_quant_tag(models.Model):
    _name = "stock.quant.tag"
    _description = " Stock Quant Tag"

    name = fields.Char(string="Name")


class stock_picking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def write(self, vals):
        res = super(stock_picking, self).write(vals)
        if 'invoice_id' in vals:
            for picking in self:
                for move in picking.move_lines:
                    if move.location_id.usage == 'supplier':
                        move.quant_ids.write({'invoice_id': vals['invoice_id']})

        return res


class stock_quant(models.Model):
    _inherit = "stock.quant"

    inventory_value = fields.Float(store=True)
    categ_id = fields.Many2one('product.category', string='Internal Category', related="product_id.categ_id",
                               store=True, readonly=True)

    input_price = fields.Float(string='Input Price')
    output_price = fields.Float(string='Output Price')
    input_date = fields.Date(string='Input date')  # exista deja un camp care se cheama in_date nu o fi bun ala ?
    output_date = fields.Date(string='Output date')
    input_amount = fields.Float(string="Input Amount", compute="_compute_input_amount", store=True)
    output_amount = fields.Float(string="Output Amount", compute="_compute_output_amount", store=True)

    customer_id = fields.Many2one('res.partner', string='Customer')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    origin = fields.Char(string='Source Document')
    invoice_id = fields.Many2one('account.invoice', string="Invoice")  # de vanzare

    note = fields.Char(string="Note")
    tag_ids = fields.Many2many('stock.quant.tag', 'stock_quant_tags', 'quant_id', 'tag_id', string="Tags")

    @api.one
    def _compute_name(self):
        """ Forms complete name of location from parent location to child location. """
        super(stock_quant, self)._compute_name()
        if self.supplier_id:
            self.name = '[' + self.supplier_id.name + ']' + self.name

    @api.multi
    def update_input_output(self):
        for quant in self:
            quant.history_ids.update_quant_partner()
            quant._compute_input_amount()
            quant._compute_output_amount()

    @api.multi
    def update_all_input_output(self):
        quants = self.search([])
        quants.update_input_output()

    @api.multi
    @api.depends('input_price')
    def _compute_input_amount(self):
        for quant in self:
            quant.input_amount = quant.input_price * quant.qty

    @api.multi
    @api.depends('output_price')
    def _compute_output_amount(self):
        for quant in self:
            quant.output_amount = quant.output_price * quant.qty


class stock_move(models.Model):
    _inherit = "stock.move"

    @api.multi
    def update_quant_partner(self):
        for move in self:
            value = {}
            if move.picking_id:

                value = {'origin': move.picking_id.origin}
                if move.location_dest_id.usage == 'customer' and move.location_id.usage == 'internal':
                    if move.picking_id.partner_id:
                        value['customer_id'] = move.picking_id.partner_id.id
                    value['output_date'] = move.picking_id.date_done
                    price_invoice = move.price_unit
                    sale_line = move.procurement_id.sale_line_id
                    if sale_line:
                        price_invoice = sale_line.price_subtotal / sale_line.product_uom_qty
                        price_invoice = sale_line.order_id.company_id.currency_id._get_conversion_rate(
                            sale_line.order_id.currency_id, move.company_id.currency_id) * price_invoice
                    else:
                        # Vanzare din POS
                        pos_order = self.env['pos.order'].search([('picking_id', '=', move.picking_id.id)])
                        if pos_order:
                            for line in pos_order.lines:
                                if line.product_id == move.product_id:
                                    price_invoice = line.price_subtotal / line.qty
                    value['output_price'] = price_invoice

                if move.location_id.usage == 'supplier' and move.location_dest_id.usage == 'internal':
                    if move.picking_id.partner_id:
                        value['supplier_id'] = move.picking_id.partner_id.id
                    value['input_date'] = move.picking_id.date_done
                    value['input_price'] = move.price_unit

                if move.location_id.usage == 'inventory' and move.location_dest_id.usage == 'internal':
                    value['input_date'] = move.picking_id.date_done
                    value['input_price'] = move.price_unit
                    if not move.price_unit and move.product_id.seller_ids:
                        value['input_price'] = move.product_id.seller_ids[0].price

                if value:
                    move.quant_ids.write(value)

    @api.multi
    def action_done(self):
        res = super(stock_move, self).action_done()
        self.update_quant_partner()
        return res
