# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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


from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp
#import odoo.workflow as workflow


class stock_move(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _create_invoice_line_from_vals(self, move, invoice_line_vals):
        invoice_line_id = super(stock_move, self)._create_invoice_line_from_vals(move, invoice_line_vals)
        move.picking_id.write({'invoice_id': invoice_line_vals['invoice_id']})
        return invoice_line_id


class stock_picking(models.Model):
    _inherit = "stock.picking"

    # camp pt a indica din ce picking se face stornarea
    origin_refund_picking_id = fields.Many2one('stock.picking', string='Origin Picking', copy=False)
    # camp prin care se indica prin ce picking se face rambursarea
    # posibil sa fie necesare mai multe intrari many2many
    refund_picking_id = fields.Many2one('stock.picking', string='Refund Picking', copy=False)

    with_refund = fields.Boolean(
        string="With refund", help="Picking list with refund or is an refund", compute="_compute_with_refund", store=False)

    @api.one
    @api.depends('origin_refund_picking_id', 'refund_picking_id')
    def _compute_with_refund(self):
        for picking in self:
            if picking.origin_refund_picking_id or picking.refund_picking_id:
                picking.with_refund = True
            else:
                picking.with_refund = False
