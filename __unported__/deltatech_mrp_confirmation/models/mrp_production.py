# -*- coding: utf-8 -*-


from odoo import api, fields,models
from odoo.tools import float_compare


class MrpProduction(models.Model):
    _inherit = 'mrp.production'



    @api.multi
    def button_plan(self):
        res = super(MrpProduction, self).button_plan()
        for production in self:
            production.generate_finished_lot_ids()
        return res



    def generate_finished_lot_ids(self):
        """ Generate stock move lots """
        self.ensure_one()
        MoveLot = self.env['stock.move.lots']
        tracked_moves = self.move_finished_ids.filtered(
            lambda move: move.state not in ('done', 'cancel') and move.product_id.tracking != 'none')
        for move in tracked_moves:
            qty = move.product_uom_qty
            if move.product_id.tracking != 'none':
                if move.product_id.tracking == 'serial':
                    while float_compare(qty, 0.0, precision_rounding=move.product_uom.rounding) > 0:
                        lot = self.env['stock.production.lot'].create(
                            {'name': self.env['ir.sequence'].next_by_code('stock.lot.serial'),
                             'product_id': move.product_id.id})
                        MoveLot.create({
                            'lot_id': lot.id,
                            'lot_produced_id': lot.id,
                            'move_id': move.id,
                            'quantity': min(1, qty),
                            'production_id': self.id,
                            'product_id': move.product_id.id,
                            #'done_wo': False,
                        })
                        qty -= 1
                else:
                    lot = self.env['stock.production.lot'].create(
                        {'name': self.env['ir.sequence'].next_by_code('stock.lot.serial'),
                         'product_id': move.product_id.id})
                    MoveLot.create({
                        'lot_id': lot.id,
                        'lot_produced_id': lot.id,
                        'move_id': move.id,
                        'quantity': qty,
                        'product_id': move.product_id.id,
                        'production_id': self.id,
                        #'done_wo': False,
                    })
