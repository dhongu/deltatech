# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _


class MRPSummary(models.TransientModel):
    _name = 'mrp.summary'

    location_id = fields.Many2one('stock.location', domain=[('usage', '=', 'production')], required=True, )
    date_range_id = fields.Many2one('date.range', string='Date range')
    date_from = fields.Date('Start Date', required=True, default=fields.Date.today)
    date_to = fields.Date('End Date', required=True, default=fields.Date.today)

    line_ids = fields.One2many('mrp.summary.line','report_id')

    @api.onchange('date_range_id')
    def onchange_date_range_id(self):
        """Handle date range change."""
        if self.date_range_id:
            self.date_from = self.date_range_id.date_start
            self.date_to = self.date_range_id.date_end

    @api.multi
    def do_compute(self):
        products = self.env['product.product']
        lines = {}

        # determinare consumuri
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '=', 'done'),
            ('location_dest_id', '=', self.location_id.id),
        ]
        moves = self.env['stock.move'].search(domain)
        for move in moves:
            products |= move.product_id
            if not move.product_id.id in lines:
                lines[move.product_id.id] = {
                    'report_id': self.id,
                    'product_id': move.product_id.id,
                    'qty': -1 * move.product_qty,
                    'amount': -1 * move.price_unit * move.product_qty
                }
            else:
                lines[move.product_id.id]['qty'] -= move.product_qty
                lines[move.product_id.id]['amount'] -= move.price_unit * move.product_qty

        #
        # determinare obtinut
        domain = [
            ('date', '>=', self.date_from),
            ('date', '<=', self.date_to),
            ('state', '=', 'done'),
            ('location_id', '=', self.location_id.id),
        ]

        moves = self.env['stock.move'].search(domain)
        for move in moves:
            products |= move.product_id
            if not move.product_id.id in lines:
                lines[move.product_id.id] = {
                    'report_id': self.id,
                    'product_id': move.product_id.id,
                    'qty': move.product_qty,
                    'amount': move.price_unit * move.product_qty
                }
            else:
                lines[move.product_id.id]['qty'] += move.product_qty
                lines[move.product_id.id]['amount'] += move.price_unit * move.product_qty

        for product in products:
            accounts = product.product_tmpl_id.get_product_accounts()

            line = lines[product.id]
            line['categ_id'] = product.categ_id.id
            if line['qty'] <= 0:
                line['type'] = 'consumed'
                line['consumed'] = -1 * line['qty']
                line['amount'] = -1 * line['amount']
                line['account_id'] = accounts['expense'].id
            else:
                line['type'] = 'obtained'
                line['obtained'] = line['qty']
                line['account_id'] = accounts['expense'].id

            self.env['mrp.summary.line'].create(line)

    def button_show(self):
        self.do_compute()
        action = self.env.ref('deltatech_mrp_report.action_mrp_summary_line').read()[0]
        action['domain'] = [('report_id', '=', self.id)]
        action['context'] = {
            'active_id': self.id,
        }
        return action

    def button_print(self):
        self.do_compute()
        records = self
        report_name = 'deltatech_mrp_report.action_report_mrp_summary'
        report = self.env.ref(report_name).report_action(records)
        return report


class MRPSummaryLine(models.TransientModel):
    _name = 'mrp.summary.line'

    report_id = fields.Many2one('mrp.summary')
    type = fields.Selection([('consumed', 'Consumed'), ('obtained', 'Obtained')])
    product_id = fields.Many2one('product.product')
    account_id = fields.Many2one('account.account')
    categ_id = fields.Many2one('product.category')
    qty = fields.Float(string='Quantity')
    consumed = fields.Float(string='Consumed')
    obtained = fields.Float(string='Obtained')
    amount = fields.Float()
