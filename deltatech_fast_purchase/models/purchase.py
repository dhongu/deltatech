# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.exceptions import UserError, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.float_utils import float_compare
from odoo.tools import safe_eval


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def receipt_to_stock(self):
        for purchase_order in self:
            for picking in purchase_order.picking_ids:
                if picking.state == 'confirmed':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(_("The stock transfer cannot be validated!"))
                if picking.state == 'assigned':
                    picking.write({'notice': False, 'origin': purchase_order.partner_ref or self.name})
                    for move_line in picking.move_lines:
                        if move_line.product_uom_qty > 0 and move_line.quantity_done == 0:
                            move_line.write({'quantity_done': move_line.product_uom_qty})
                        else:
                            move_line.unlink()
                    # pentru a se prelua data din comanda de achizitie
                    picking.with_context(force_period_date=purchase_order.date_order).action_done()

    def action_button_confirm_to_invoice(self):
        if self.state == 'draft':
            self.button_confirm()  # confirma comanda

        params = self.env['ir.config_parameter'].sudo()

        validate_invoice = params.get_param('fast_purchase.validate_invoice', default='True')
        validate_invoice = safe_eval(validate_invoice)

        self.receipt_to_stock()

        action = self.action_view_invoice()

        if not self.invoice_ids:
            # result['target'] = 'new'
            if not action['context']:
                action['context'] = {}
            # action['context']['default_date_invoice'] = self.date_order
            action['views'] = [[False, "form"]]

            vals = {
                'purchase_id': self.id,
               # 'type': action['context']['type'],
                'invoice_date': self.date_order.date(),
                'ref': self.partner_ref
            }
            invoice = self.env['account.move'].with_context(action['context']).new(vals)
            invoice._onchange_purchase_auto_complete()

            inv = invoice._convert_to_write(invoice._cache)
            new_invoice = self.env['account.move'].with_context(action['context']).create(inv)
            res = self.env.ref('account.invoice_supplier_form', False)
            action['views'] = [(res and res.id or False, 'form')]
            action['res_id'] = new_invoice.id
            if validate_invoice:
                # new_invoice.action_invoice_open()  de vazut cum se valideaza factura
                action = False
        return action


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

    def action_view_invoice(self):
        action = super(PurchaseOrder, self).action_view_invoice()
        invoice_type = 'in_invoice'
        for line in self.order_line:
            if line.product_id.purchase_method == 'purchase':
                qty = line.product_qty - line.qty_invoiced
            else:
                qty = line.qty_received - line.qty_invoiced
            if qty < 0:
                invoice_type = 'in_refund'
        action['context']['default_type'] = invoice_type
        action['context']['default_invoice_date'] = self.date_planned
        return action


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'


    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        if move.type == 'in_refund':
            if self.product_id.purchase_method == 'purchase':
                qty = self.qty_invoiced - self.product_qty
            else:
                qty = self.qty_invoiced - self.qty_received
            if float_compare(qty, 0.0, precision_rounding=self.product_uom.rounding) <= 0:
                qty = 0.0
            res['quantity'] = qty
        return res
