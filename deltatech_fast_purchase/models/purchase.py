# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.exceptions import UserError, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    @api.multi
    def action_button_confirm_to_invoice(self):
        if self.state == 'draft':
            self.button_confirm()  # confirma comanda

        for picking in self.picking_ids:
            if picking.state == 'assigned':
                picking.write({'notice': False})
                for move_line in picking.move_lines:
                    if move_line.product_uom_qty > 0 and move_line.quantity_done == 0:
                        move_line.write({'quantity_done': move_line.product_uom_qty})
                    else:
                        move_line.unlink()
                picking.action_done()

        action = self.action_view_invoice()

        if not self.invoice_ids:
            # result['target'] = 'new'
            if not action['context']:
                action['context'] = {}
            action['context']['default_date_invoice'] = self.date_order[:10]
            action['views'] = [[False, "form"]]
        return action

    @api.multi
    def action_button_confirm_notice(self):

        picking_ids = self.env['stock.picking']
        for picking in self.picking_ids:
            if picking.state == 'assigned':
                picking.write({'notice': True})
                picking_ids |= picking

        if not picking_ids:
            return

        action = self.env.ref('stock.action_picking_tree')
        result = action.read()[0]

        result['context'] = {}

        pick_ids = picking_ids.ids
        # choose the view_mode accordingly
        if len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = picking_ids.id
        return result

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
