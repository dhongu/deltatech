# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import api
from odoo import models
from odoo.exceptions import Warning
from odoo.tools.translate import _


class stock_move(models.Model):
    _inherit = 'stock.move'

    # metoda standard copiata si am comentat actualizarea pretului
    def _store_average_cost_price(self):
        """ Store the average price of the move on the move and product form (costing method 'real')"""
        for move in self.filtered(lambda move: move.product_id.cost_method == 'fifo'):
            # product_obj = self.pool.get('product.product')
            if any(q.qty <= 0 for q in move.quant_ids) or move.product_qty == 0:
                # if there is a negative quant, the standard price shouldn't be updated
                return
            # Note: here we can't store a quant.cost directly as we may have moved out 2 units
            # (1 unit to 5€ and 1 unit to 7€) and in case of a product return of 1 unit, we can't
            # know which of the 2 costs has to be used (5€ or 7€?). So at that time, thanks to the
            # average valuation price we are storing we will valuate it at 6€
            valuation_price = sum(q.qty * q.cost for q in move.quant_ids)
            average_valuation_price = valuation_price / move.product_qty

            # move.product_id.with_context(force_company=move.company_id.id).sudo().write(
            #    {'standard_price': average_valuation_price})
            move.write({'price_unit': average_valuation_price})

        for move in self.filtered(
                lambda move: move.product_id.cost_method != 'real' and not move.origin_returned_move_id):
            # Unit price of the move should be the current standard price, taking into account
            # price fluctuations due to products received between move creation (e.g. at SO
            # confirmation) and move set to done (delivery completed).
            move.write({'price_unit': move.product_id.standard_price})


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    # ajustare automata a monedei de facturare in conformitate cu moneda din jurnal
    @api.multi
    def action_invoice_create(self, journal_id, group=False, type='out_invoice'):
        for picking in self:
            if picking.state != 'done':
                raise Warning(_("The picking list %s isn't transferred.") % picking.name)
        invoices = super(stock_picking, self).action_invoice_create(journal_id, group, type)

        # this = self.with_context(inv_type=type)  # foarte important pt a determina corect moneda

        # self = this

        journal = self.env['account.journal'].browse(journal_id)
        obj_invoices = self.env['account.invoice'].browse(invoices)

        to_currency = journal.currency or self.env.user.company_id.currency_id

        for obj_inv in obj_invoices:
            if to_currency == obj_inv.currency_id:
                continue
            from_currency = obj_inv.currency_id.with_context(date=obj_inv.date_invoice)

            for line in obj_inv.invoice_line_ids:
                new_price = from_currency.compute(line.price_unit, to_currency)
                line.write({'price_unit': new_price})

            obj_inv.write({'currency_id': to_currency.id})
            obj_inv.button_compute()
        return invoices

    @api.model
    def _create_invoice_from_picking(self, picking, vals):
        invoice_id = super(stock_picking, self)._create_invoice_from_picking(picking, vals)
        if picking.sale_id:
            picking.sale_id.write({'invoice_ids': [(4, invoice_id)]})
        picking.write({'invoice_id': invoice_id})

        return invoice_id

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
