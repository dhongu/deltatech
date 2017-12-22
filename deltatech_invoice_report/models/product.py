# -*- coding: utf-8 -*-


from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp


class product_template(models.Model):
    _inherit = 'product.template'

    invoice_count = fields.Integer(compute='_compute_invoice_count')

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
        action[
            'context'] = """{
             'group_by':['date:year'],
             'measures': ['product_qty', 'price_average'],
             'col_group_by': ['type'] ,
              'group_by_no_leaf': 1,
              'search_disable_custom_filters': True
             }"""
        #
        action['domain'] = "[('product_id','in',[" + ','.join(map(str, products.ids)) + "])]"
        return action
