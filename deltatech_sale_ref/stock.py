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



from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare

from datetime import datetime
import logging

from cStringIO import StringIO
import csv
import base64
 
_logger = logging.getLogger(__name__)


class stock_transfer_details_items(models.TransientModel):
    _inherit = 'stock.transfer_details_items'
    _order = 'product_id'

    # ref = fields.Char(string="Reference", related="packop_id.ref" , copy=True, store=True)  #related=False
    ref = fields.Char(string="Reference", related=False , copy=True, store=True)

class stock_transfer_details(models.TransientModel):
    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self):
        """
        override for packing operations numbering
        :return:
        """
        if self.picking_id.state not in ['assigned', 'partially_available']:
            raise Warning(_('You cannot transfer a picking in state \'%s\'.') % self.picking_id.state)

        processed_ids = []
        # Create new and update existing pack operations
        for lstits in [self.item_ids, self.packop_ids]:
            for prod in lstits:
                pack_datas = {
                    'product_id': prod.product_id.id,
                    'product_uom_id': prod.product_uom_id.id,
                    'product_qty': prod.quantity,
                    'package_id': prod.package_id.id,
                    'lot_id': prod.lot_id.id,
                    'location_id': prod.sourceloc_id.id,
                    'location_dest_id': prod.destinationloc_id.id,
                    'result_package_id': prod.result_package_id.id,
                    'date': prod.date if prod.date else datetime.now(),
                    'owner_id': prod.owner_id.id,
                }
                if prod.packop_id:
                    prod.packop_id.with_context(no_recompute=True).write(pack_datas)
                    processed_ids.append(prod.packop_id.id)
                else:
                    pack_datas['picking_id'] = self.picking_id.id
                    packop_id = self.env['stock.pack.operation'].create(pack_datas)
                    processed_ids.append(packop_id.id)
        packops_ids = self.env['stock.pack.operation'].browse(processed_ids)
        # ordered_packops = packops_ids.sorted(lambda p: p.product_id)
        products = self.env['product.product']
        for packop in packops_ids:
            products |= packop.product_id
        if products:
            for product in products:
                packops_filtered = packops_ids.filtered(lambda p: p.product_id == product)
                packops_referenced = packops_filtered.filtered(lambda r: r.ref != False)
                packops_filtered.get_number()
                packops_filtered.write({"ref": packops_referenced.ref})
        # Delete the others
        packops = self.env['stock.pack.operation'].search(
            ['&', ('picking_id', '=', self.picking_id.id), '!', ('id', 'in', processed_ids)])
        packops.unlink()

        # Execute the transfer of the picking
        self.picking_id.do_transfer()

        return True


class stock_pack_operation(models.Model):
    _inherit = "stock.pack.operation"
    
    ref = fields.Char(string="Reference", copy=False)
    label_sequence = fields.Char(string="Label Reference", copy=False)

    @api.model
    def get_number(self):
        sequence = self.env.ref("deltatech_sale_ref.packing_operations_sequence")
        for pack_operation in self:
            pack_operation.write({'label_sequence': self.env['ir.sequence'].next_by_id(sequence.id)})
 
class stock_move(models.Model):
    _inherit = "stock.move"

    ref = fields.Char(string="Reference", related='procurement_id.sale_line_id.ref', copy=True)

    def _get_invoice_line_vals(self, cr, uid, move, partner, inv_type, context=None):
        res = super(stock_move, self)._get_invoice_line_vals(cr, uid, move, partner, inv_type, context=context)
        if inv_type in ('out_invoice', 'out_refund') and move.procurement_id and move.procurement_id.sale_line_id:
            sale_line = move.procurement_id.sale_line_id 
            res['ref'] = sale_line.ref
         
        return res
 

    @api.multi
    def _picking_assign(self, procurement_group, location_from, location_to):
        res = super(stock_move, self)._picking_assign( procurement_group, location_from, location_to)
        
        move_group_by_date = {}
        picking = self[0].picking_id
        for move in self:
            key = move.date[:10]
            move_group_by_date.setdefault(key, {'moves':self.env['stock.move'],'picking':False})
            
            move_group_by_date[key]['moves'] |=  move
            if picking:
                move_group_by_date[key]['picking'] = picking
            picking = False
       
        for key in move_group_by_date:
            moves = move_group_by_date[key]['moves']
            picking = move_group_by_date[key]['picking']
            if not picking:
                values = self._prepare_picking_assign(moves[0])
                picking = self.env["stock.picking"].create(values)
                moves.write({'picking_id': picking.id})

        

class stock_quant(models.Model):
    _inherit = "stock.quant"

    ref = fields.Char(string="Reference", related='history_ids.ref')
    
class stock_picking(models.Model):
    _inherit= "stock.picking"

     # metoda redefiniat pentru a nu mai uni produsele care sunt din miscari diferite
    @api.cr_uid_ids_context
    def do_prepare_partial(self, cr, uid, picking_ids, context=None):
        context = context or {}
        pack_operation_obj = self.pool.get('stock.pack.operation')
        #used to avoid recomputing the remaining quantities at each new pack operation created
        ctx = context.copy()
        ctx['no_recompute'] = True

        #get list of existing operations and delete them
        existing_package_ids = pack_operation_obj.search(cr, uid, [('picking_id', 'in', picking_ids)], context=context)
        if existing_package_ids:
            pack_operation_obj.unlink(cr, uid, existing_package_ids, context)
        
        self.back_order_for_multi_prod(cr, uid, picking_ids, context=context)
            
        for picking in self.browse(cr, uid, picking_ids, context=context):
            
            picking_quants = []
            #Calculate packages, reserved quants, qtys of this picking's moves
            for move in picking.move_lines:
                forced_qties = {}  # Quantity remaining after calculating reserved quants
                if move.state not in ('assigned', 'confirmed', 'waiting'):
                    continue
                move_quants = move.reserved_quant_ids
                picking_quants += move_quants
                forced_qty = (move.state == 'assigned') and move.product_qty - sum([x.qty for x in move_quants]) or 0
                #if we used force_assign() on the move, or if the move is incoming, forced_qty > 0
                if float_compare(forced_qty, 0, precision_rounding=move.product_id.uom_id.rounding) > 0:
                    if forced_qties.get(move.product_id):
                        forced_qties[move.product_id] += forced_qty
                    else:
                        forced_qties[move.product_id] = forced_qty
                pack_operations_values = self._prepare_pack_ops(cr, uid, picking, picking_quants, forced_qties, context=context)
                for vals in pack_operations_values:
                    # sequence = self.pool.get('stock.pack.operation')._get_default_ref_sequence(cr, uid, context=context)

                    # sequence = self.env.ref("deltatech_sale_ref.packing_operations_sequence")
                    # if sequence:
                    #     vals["ref"] = sequence
                    # vals["ref"] = pack_operation_obj._get_default_ref_sequence()
                    if move.ref:
                        vals['ref'] = move.ref
                    pack_operation_obj.create(cr, uid, vals, context=ctx)
        #recompute the remaining quantities all at once
        self.do_recompute_remaining_quantities(cr, uid, picking_ids, context=context)
        self.write(cr, uid, picking_ids, {'recompute_pack_op': False}, context=context)


    @api.multi
    def back_order_for_multi_prod(self):
        """ Creare comanda restanta pentru produsele care se repeta"""
        for picking in self:
             cont = True
             sec_picking = False
             while cont:
                cont = False
                for move1 in picking.move_lines:
                    for move2 in picking.move_lines:
                        if move1.id != move2.id and move1.product_id.id == move2.product_id.id:
                            cont = True
                            if not sec_picking:
                                sec_picking = picking.copy({'backorder_id':picking.id,'move_lines':False})
                            move1.write({'picking_id':sec_picking.id})

    @api.multi
    def generate_csv_pack_report(self):
        self.ensure_one()
        field_names = [
            "Order ref.",
            "Product code",
            "Product name",
            "Unit of Measure",
            "Quantity",
            "Line reference",
            "Label reference",
            "Delivery date",
            "Package gross weight",
            "Package net weight",
        ]  # Field names for CSV headers
        data = StringIO()
        writer = csv.DictWriter(data, fieldnames=field_names)
        writer.writeheader()
        for pack_line in self.pack_operation_ids:
            row = {
                "Order ref.": self.sale_id.client_order_ref,
                "Product code": pack_line.product_id.default_code,
                "Product name": pack_line.product_id.name,
                "Unit of Measure": pack_line.product_uom_id.name,
                "Quantity": pack_line.product_qty,
                "Line reference": pack_line.ref,
                "Label reference": pack_line.label_sequence,
                "Delivery date": self.pack_date,
                "Package gross weight": self.product_id.pack_weight,
                "Package net weight": self.product_id.weight_net,
            }
            writer.writerow(row)
        file_name = "{}_packing.csv".format(self.sale_id.client_order_ref)
        csv_file = base64.encodestring(data.getvalue())

        wizard = self.env["packops.csv.wizard"].create({"csv_file": csv_file, "file_name": file_name})
        return {'view_mode': 'form',
                'res_id': wizard.id,
                'res_model': 'packops.csv.wizard',
                'view_type': 'form',
                'type': 'ir.actions.act_window',
                'target': 'new',
        }
