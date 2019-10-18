# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare

class StockPicking(models.Model):
    _inherit = 'stock.picking'


    @api.multi
    def action_view_invoice(self):
        if self.purchase_id:

            action = self.env.ref('account.action_invoice_tree2')
            result = action.read()[0]

            # override the context to get rid of the default filtering
            invoice_type = 'in_invoice'
            result['context'] = { 'default_purchase_id': self.purchase_id.id,
                                 'default_date_invoice': self.date_done}

            if self.location_id.usage == 'internal':
                invoice_type = 'in_refund'

            result['context']['type'] = invoice_type
            invoice_ids = self.purchase_id.invoice_ids.filtered(lambda r:r.type == invoice_type)

            if not invoice_ids:
                # Choose a default account journal in the same currency in case a new invoice is created
                journal_domain = [
                    ('type', '=', 'purchase'),
                    ('company_id', '=', self.purchase_id.company_id.id),
                    ('currency_id', '=', self.purchase_id.currency_id.id),
                ]
                default_journal_id = self.env['account.journal'].search(journal_domain, limit=1)
                if default_journal_id:
                    result['context']['default_journal_id'] = default_journal_id.id
            else:
                # Use the same account journal than a previous invoice
                result['context']['default_journal_id'] = invoice_ids[0].journal_id.id

            # choose the view_mode accordingly
            if len(invoice_ids) != 1:
                result['domain'] = "[('id', 'in', " + str(invoice_ids.ids) + ")]"
            elif len(invoice_ids) == 1:
                res = self.env.ref('account.invoice_supplier_form', False)
                result['views'] = [(res and res.id or False, 'form')]
                result['res_id'] = invoice_ids.id
            if not invoice_ids:
                #result['target'] = 'new'
                result['views'] = [[False, "form"]]
            return result
