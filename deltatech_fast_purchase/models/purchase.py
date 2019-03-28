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
            action['context']['default_date_invoice'] = self.date_order
            action['views'] = [[False, "form"]]

            vals = {
                'purchase_id': self.id,
                'type': action['context']['type']
            }
            invoice = self.env['account.invoice'].with_context(action['context']).new(vals)
            invoice.purchase_order_change()

            inv = invoice._convert_to_write(invoice._cache)
            new_invoice = self.env['account.invoice'].with_context(action['context']).create(inv)
            res = self.env.ref('account.invoice_supplier_form', False)
            action['views'] = [(res and res.id or False, 'form')]
            action['res_id'] = new_invoice.id
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

    def action_button_create_invoice(self):
        action = self.env.ref('account.action_invoice_tree2')
        result = action.read()[0]

        # override the context to get rid of the default filtering
        invoice_type = 'in_invoice'
        result['context'] = {'default_purchase_id': self.id,
                             'default_date_invoice': self.date_planned}


        for line in self.order_line:
            if line.product_id.purchase_method == 'purchase':
                qty = line.product_qty - line.qty_invoiced
            else:
                qty = line.qty_received - line.qty_invoiced
            if qty < 0:
                invoice_type = 'in_refund'

        result['context']['type'] = invoice_type
        invoice_ids = self.invoice_ids.filtered(lambda r: r.type == invoice_type)

        if not invoice_ids:
            # Choose a default account journal in the same currency in case a new invoice is created
            journal_domain = [
                ('type', '=', 'purchase'),
                ('company_id', '=', self.company_id.id),
                ('currency_id', '=', self.currency_id.id),
            ]
            default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
            if default_journal_id:
                result['context']['default_journal_id'] = default_journal_id.id
        else:
            # Use the same account journal than a previous invoice
            result['context']['default_journal_id'] = invoice_ids[0].journal_id.id

        # choose the view_mode accordingly
        # if len(invoice_ids) != 1:
        #     result['domain'] = "[('id', 'in', " + str(invoice_ids.ids) + ")]"
        # elif len(invoice_ids) == 1:
        #     res = self.env.ref('account.invoice_supplier_form', False)
        #     result['views'] = [(res and res.id or False, 'form')]
        #     result['res_id'] = invoice_ids.id
        # if not invoice_ids:

        result['views'] = [[False, "form"]]
        return result

