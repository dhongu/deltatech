# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _


class product_invoice_history(models.TransientModel):
    _name = 'product.invoice.history'

    product_id = fields.Many2one('product.product')
    template_id = fields.Many2one('product.template')
    year = fields.Char(string='Year')
    qty = fields.Float(string='Qty')


class product_template(models.Model):
    _inherit = 'product.template'

    invoice_count = fields.Integer(compute='_compute_invoice_count')

    invoice_history = fields.One2many('product.invoice.history', 'template_id', compute="_compute_invoice_history")

    @api.multi
    def _compute_invoice_history(self):
        for template in self:
            products = template.product_variant_ids
            domain = [
                ('type', 'in', ['out_invoice', 'out_refund']),
                ('product_id', 'in', products.ids),
            ]
            groups = self.env['account.invoice.report'].read_group(domain=domain,
                                                                   fields=['product_qty', 'date'],
                                                                   groupby=['date:year'])
            invoice_history = self.env['product.invoice.history']
            for item in groups:
                invoice_history |= self.env['product.invoice.history'].create({
                    'template_id': template.id,
                    'year': item['date:year'],
                    'qty': item['product_qty']
                })
            template.invoice_history = invoice_history

    @api.multi
    def _compute_invoice_count(self):
        products = self.env['product.product']
        for template in self:
            products = template.product_variant_ids

            domain = [
                ('type', 'in', ['in_invoice', 'in_refund']),
                ('product_id', 'in', products.ids),
            ]
            product_qty = 0
            price_average = 0.0
            groups = self.env['account.invoice.report'].read_group(domain=domain,
                                                                   fields=['product_id', 'product_qty',
                                                                           'price_average'],
                                                                   groupby=['product_id'])
            for item in groups:
                product_qty += item['product_qty']
                price_average = item['price_average']

            template.invoice_count = price_average

    @api.multi
    def action_view_invoice(self):

        action = self.env.ref('account.action_account_invoice_report_all').read()[0]
        products = self.env['product.product']
        for template in self:
            products |= template.product_variant_ids
        action['context'] = """{
             'group_by':['date:year'],
             'measures': ['product_qty', 'price_average'],
             'col_group_by': ['type'] ,
              'group_by_no_leaf': 1,
              'search_disable_custom_filters': True
             }"""
        #
        action['domain'] = "[('product_id','in',[" + ','.join(map(str, products.ids)) + "])]"
        return action


class product_product(models.Model):
    _inherit = 'product.product'

    @api.multi
    def action_view_invoice(self):
        action = self.env.ref('account.action_account_invoice_report_all').read()[0]
        action['context'] = """{
             'group_by':['date:year'],
             'measures': ['product_qty', 'price_average'],
             'col_group_by': ['type'] ,
              'group_by_no_leaf': 1,
              'search_disable_custom_filters': True
             }"""
        #
        action['domain'] = "[('product_id','in',[" + ','.join(map(str, self.ids)) + "])]"
        return action
