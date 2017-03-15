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
    customer_id = fields.Many2one('res.partner', string='Customer')
    supplier_id = fields.Many2one('res.partner', string='Supplier')
    origin = fields.Char(string='Source Document')
    invoice_id = fields.Many2one('account.invoice', string="Invoice")

    note = fields.Char(string="Note")
    tag_ids = fields.Many2many('stock.quant.tag', 'stock_quant_tags', 'quant_id', 'tag_id', string="Tags")


    #todo: de scris in new api
    def _get_quant_name(self, cr, uid, ids, name, args, context=None):
        """ Forms complete name of location from parent location to child location.
        @return: Dictionary of values
        """
        res = {}
        for q in self.browse(cr, uid, ids, context=context):

            res[q.id] = q.product_id.code or ''
            if q.lot_id:
                res[q.id] = q.lot_id.name

            if q.supplier_id:
                res[q.id] += '[' + q.supplier_id.name + ']'

            res[q.id] += ': ' + str(q.qty) + q.product_id.uom_id.name

        return res


class stock_move(models.Model):
    _inherit = "stock.move"

    @api.multi
    def update_quant_partner(self):
        for move in self:
            value = {}
            if move.picking_id:
                if move.picking_id.partner_id:
                    value = {'origin': move.picking_id.origin}
                    if move.location_dest_id.usage == 'customer':
                        value['customer_id'] = move.picking_id.partner_id.id
                    if move.location_id.usage == 'supplier':
                        value['supplier_id'] = move.picking_id.partner_id.id
                        if move.picking_id._columns.get('invoice_id'):  # este instalat modulul stock_picking_invoice_link
                            if move.picking_id.invoice_id:
                                value['invoice_id'] = move.picking_id.invoice_id.id
                if value:
                    move.quant_ids.write(value)

    @api.multi
    def action_done(self):
        res = super(stock_move, self).action_done()
        self.update_quant_partner()
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
