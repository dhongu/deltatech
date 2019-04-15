# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp


class StockSimpleTransfer(models.TransientModel):
    _name = 'stock.simple.transfer'

    product_id = fields.Many2one('product.product', string='Product', required=True)
    partner_id = fields.Many2one('res.partner', string='Partner')
    picking_type_id = fields.Many2one('stock.picking.type', string="Picking type", required=True)
    date = fields.Date(string='Date', default=fields.Date.today, required=True)

    quantity = fields.Float(string="Quantity", digits= dp.get_precision('Product Unit of Measure'), required=True)
    uom_id = fields.Many2one('product.uom', 'Unit of Measure', required=True)


    @api.onchange('product_id')
    def onchange_product_id(self):
        self.uom_id = self.product_id.uom_id

    @api.multi
    def do_transfer(self):



        context = {'default_picking_type_id': self.picking_type_id.id}
        picking = self.env['stock.picking'].with_context(context).create({
            'picking_type_id': self.picking_type_id.id,
            'date': self.date,
            'partner_id':self.partner_id,
        })



        self.add_picking_line(picking=picking, product= self.product_id, quantity=self.quantity, uom=self.uom_id)


        if picking.move_lines:
            picking.action_assign()
            picking.button_validate()
            if picking.state == 'assigned':
                for move in picking.move_lines:
                    for move_line in move.move_line_ids:
                        move_line.qty_done = move_line.product_uom_qty
            picking.action_done()



        return {
            'domain': [('id', 'in', [picking.id])],
            'name': _('Consumption & Receipt'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'view_id': False,
            'context': {},
            'type': 'ir.actions.act_window'
        }

    def add_picking_line(self, picking, product, quantity, uom):
        move = self.env['stock.move'].search([('picking_id', '=', picking.id),
                                              ('product_id', '=', product.id),
                                              ('product_uom', '=', uom.id)])
        if move:
            qty = move.product_uom_qty + quantity
            move.write({'product_uom_qty': qty})
        else:
            values = {
                'state': 'confirmed',
                'product_id': product.id,
                'product_uom': uom.id,
                'product_uom_qty': quantity,
               # 'quantity_done': quantity,  # o fi bine >???
                'name': product.name,
                'picking_id': picking.id,
                'location_id': picking.picking_type_id.default_location_src_id.id,
                'location_dest_id': picking.picking_type_id.default_location_dest_id.id
            }

            move = self.env['stock.move'].create(values)
        return move
