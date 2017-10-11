# -*- coding: utf-8 -*-




from odoo import models, fields, api


class StockPickingWave(models.Model):
    _inherit = "stock.picking.wave"

    carrier_id = fields.Many2one("delivery.carrier", string="Carrier", readonly=True,
                                 states={'draft': [('readonly', False)]})

    mean_transp = fields.Char(string='Mean transport', readonly=True,
                              states={'draft': [('readonly', False)]})

    date_expected = fields.Datetime('Expected Date', default=fields.Datetime.now, index=True,
                                    required=True, readonly=True,
                                    states={'draft': [('readonly', False)]})

    move_ids = fields.Many2many('stock.move', compute="_compute_move", string="Stock Moves")

    @api.multi
    def _compute_move(self):
        for wave in self:
            moves = self.env['stock.move']
            for picking in wave.picking_ids:
                moves |= picking.move_lines
            wave.move_ids = moves

    @api.multi
    def button_plan(self):
        for wave in self:
            moves = self.env['stock.move']
            pickings = self.env['stock.picking']

            for picking in wave.picking_ids:
                for move in picking.move_lines:
                    if move.state not in ['done', 'cancel']:
                        moves |= move
                if picking.state not in ['done', 'cancel']:
                    pickings |= picking

            if moves:
                moves.write({'date_expected': wave.date_expected})
            if pickings:
                pickings.write({'mean_transp': wave.mean_transp,
                                'carrier_id': wave.carrier_id.id})
