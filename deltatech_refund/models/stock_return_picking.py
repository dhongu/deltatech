# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
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


from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
import openerp.addons.decimal_precision as dp


class stock_return_picking(models.TransientModel):
    _inherit = "stock.return.picking"

    make_new_picking = fields.Boolean(string="Make a new picking", default=False,
                                      help="If is active, a new picking list will be created")

    do_transfer = fields.Boolean(string="Do transfer", default=True,
                                 help="If is active, refund picking list will be transferred automatically")

    transfer_date = fields.Datetime(string="Transfer Date", default=lambda *a: fields.Datetime.now())
    note = fields.Char(string='Note', readonly=True)
    reason = fields.Char(string='Reason')

    @api.model
    def default_get(self, fields):
        res = super(stock_return_picking, self).default_get(fields)

        record_id = self.env.context and self.env.context.get('active_id', False) or False
        pick = self.env['stock.picking'].browse(record_id)
        if pick.origin_refund_picking_id:
            #    raise Warning(_('This document is a return for %s') % pick.origin_refund_picking_id.name)
            res['note'] = _('This document is a refund for %s') % pick.origin_refund_picking_id.name
        if pick.refund_picking_id:
            # raise Warning(_('This document was be already returned by %s') % pick.refund_picking_id.name)
            res['note'] = _('This document was be already refunded by %s') % pick.refund_picking_id.name

        new_moves = []
        for prod_ret in res.get('product_return_moves', []):
            move_id = prod_ret['move_id']
            move = self.env['stock.move'].browse(move_id)
            for quant in move.quant_ids:
                if quant.lot_id:
                    if not prod_ret.get('lot_id', False):
                        prod_ret['lot_id'] = quant.lot_id.id
                        prod_ret['quantity'] = quant.qty
                    else:
                        new_line = prod_ret.copy()
                        new_line['lot_id'] = quant.lot_id.id
                        new_line['quantity'] = quant.qty
                        new_moves.append(new_line)
        if new_moves:
            res['product_return_moves'].append(new_line)
        return res

    @api.model
    def get_link(self, model):
        for model_id, model_name in model.name_get():
            link = "<a href='#id=%s&model=%s'>%s</a>" % (str(model_id), model._name, model_name)
        return link

    @api.multi
    def _create_returns(self):

        record_id = self.env.context and self.env.context.get('active_id', False) or False
        pick = self.env['stock.picking'].browse(record_id)

        if self.make_new_picking:
            # mai sunt toate produsele de locul lor ?
            qty_pick = 0
            for move in pick.move_lines:
                qty_pick += move.product_qty
            qty_return = 0
            for move in self.product_return_moves:
                qty_return += move.quantity
            if qty_return != qty_pick:
                raise Warning(_('Unable to prepare a new picking list with all quantity '))

        new_picking_id, pick_type_id = super(stock_return_picking, self)._create_returns()
        pick_return = self.env['stock.picking'].browse(new_picking_id)

        # todo: de pus numele sub forma de link <a href="model=stock.picking&id=">pick_return.name</a>
        # http://192.168.45.132:8069/web?#action=mail.action_mail_redirect&model=stock.picking&res_id=59
        #   #id=59&view_type=form&model=stock.picking
        msg = _('Picking list %s was refunded by %s ') % (self.get_link(pick), self.get_link(pick_return))
        pick.message_post(body=msg)
        pick_return.message_post(body=msg)

        pick_return.write({'date': self.transfer_date,
                           'origin': pick.origin,
                           'note': self.reason,
                           'origin_refund_picking_id': pick.id})

        pick.write({'refund_picking_id': pick_return.id})

        """
        modificarea datei se face in modulul stock_date
        for move in pick_return.move_lines:
            move.with_context(exact_date=True).write({'date':   self.transfer_date, 
                        'date_expected':self.transfer_date })
        """

        if self.make_new_picking:

            pick_backorder = pick_return.copy({
                'picking_type_id': pick.picking_type_id.id,
                'state': 'draft',
                'backorder_id': pick.id,
                'origin': pick.origin,
                'move_lines': [],
            })

            msg = _('%s was generated to transfer products from %s they have been refunded by %s ') % (
                self.get_link(pick_backorder),
                self.get_link(pick),
                self.get_link(pick_return))
            pick.message_post(body=msg)
            pick_backorder.message_post(body=msg)

            for move in pick_return.move_lines:
                move.write({'purchase_line_id': move.origin_returned_move_id.purchase_line_id.id, })

                new_move = move.copy({'location_id': move.origin_returned_move_id.location_id.id,
                                      'location_dest_id': move.origin_returned_move_id.location_dest_id.id,
                                      'state': 'draft',
                                      'picking_id': pick_backorder.id})

                new_move.write({'purchase_line_id': move.origin_returned_move_id.purchase_line_id.id, })
            pick_backorder.action_confirm()
            pick_backorder.action_assign()
        else:
            msg = _(
                'It was not generated a new picking list for transfer products from %s they have been refunded by %s ') % (
                      self.get_link(pick),
                      self.get_link(pick_return))
            pick.message_post(body=msg)
        if self.do_transfer:
            pick_return.do_transfer()

        return new_picking_id, pick_type_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
