# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
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

from openerp import models, fields, api, tools, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
from openerp.api import Environment


class stock_quant_tag(models.Model):
    _name = "stock.quant.tag"
    _description = "Stock Quant Tag"

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

    # Campuri  din versiunea 10
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
        super(stock_quant, self)._compute_name()
        if self.supplier_id:
            self.name = '[' + self.supplier_id.name + ']' + self.name



    def _get_quant_name(self, cr, uid, ids, name, args, context=None):
        res = {}
        for q in self.browse(cr, uid, ids, context=context):

            res[q.id] = q.product_id.code or ''
            if q.lot_id:
                res[q.id] = q.lot_id.name

            if q.supplier_id:
                res[q.id] += '[' + q.supplier_id.name + ']'

            res[q.id] += ': ' + str(q.qty) + q.product_id.uom_id.name

        return res






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
    @api.depends('input_price', 'qty')
    def _compute_input_amount(self):
        for quant in self:
            quant.input_amount = quant.input_price * quant.qty

    @api.multi
    @api.depends('output_price', 'qty')
    def _compute_output_amount(self):
        for quant in self:
            quant.output_amount = quant.output_price * quant.qty


class stock_move(models.Model):
    _inherit = "stock.move"

    @api.multi
    def update_quant_partner(self):
        pos_mod = self.env['ir.module.module'].search([('name', '=', 'point_of_sale'),('state', '=', 'installed')])




        for move in self:
            value = {}
            if move.picking_id:

                value = {'origin': move.picking_id.origin}
                if move.location_dest_id.usage == 'customer' and move.location_id.usage in ['internal', 'supplier']:
                    if move.picking_id.partner_id:
                        value['customer_id'] = move.picking_id.partner_id.id
                    value['output_date'] = move.date # move.picking_id.date_done
                    price_invoice = move.price_unit
                    sale_line = move.procurement_id.sale_line_id
                    if sale_line:
                        price_invoice = sale_line.price_subtotal / sale_line.product_uom_qty
                        price_invoice = sale_line.order_id.company_id.currency_id._get_conversion_rate(
                            sale_line.order_id.currency_id, move.company_id.currency_id) * price_invoice
                    else:
                        # Vanzare din POS
                        if pos_mod:
                            pos_order = self.env['pos.order'].search([('picking_id', '=', move.picking_id.id)])
                            if pos_order:
                                for line in pos_order.lines:
                                    if line.product_id == move.product_id:
                                        price_invoice = line.price_subtotal / line.qty
                    value['output_price'] = price_invoice

                if move.location_id.usage == 'supplier' and move.location_dest_id.usage in ['internal', 'customer']:
                    if move.picking_id.partner_id:
                        value['supplier_id'] = move.picking_id.partner_id.id
                    if move.invoice_line_id:
                        value['invoice_id'] = move.invoice_line_id.invoice_id.id
                    value['input_date'] = move.date #move.picking_id.date_done
                    value['input_price'] = move.price_unit

                if move.location_id.usage == 'inventory' and move.location_dest_id.usage == 'internal':
                    value['input_date'] = move.date #move.picking_id.date_done
                    value['input_price'] = move.price_unit
                    if not move.price_unit and move.product_id.seller_ids:
                        value['input_price'] = move.product_id.seller_ids[0].price



                # varianta veche
                # if move.picking_id.partner_id:
                #     value = {'origin': move.picking_id.origin}
                #     if move.location_dest_id.usage == 'customer':
                #         value['customer_id'] = move.picking_id.partner_id.id
                #     if move.location_id.usage == 'supplier':
                #         value['supplier_id'] = move.picking_id.partner_id.id
                #         if move.picking_id._columns.get('invoice_id'):  # este instalat modulul stock_picking_invoice_link
                #             if move.picking_id.invoice_id:
                #                 value['invoice_id'] = move.picking_id.invoice_id.id
                if value:
                    move.quant_ids.write(value)

    @api.multi
    def action_done(self):
        res = super(stock_move, self).action_done()
        self.update_quant_partner()
        return res

    @api.multi
    def show_picking(self):
        self.ensure_one()
        if self.picking_id:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'stock.picking',
                'view_type': 'form',
                'view_mode': 'form',
                'res_id': self.picking_id.id,
            }

    @api.multi
    def show_invoice(self):
        self.ensure_one()
        if self.picking_id:
            if self.picking_id.invoice_id:
                return {
                    'type': 'ir.actions.act_window',
                    'res_model': 'account.invoice',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_id': self.picking_id.invoice_id.id,
                }



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
