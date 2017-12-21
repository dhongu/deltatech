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
                ('product_id', 'in', products.ids),
            ]
            product_qty = 0
            groups = self.env['account.invoice.report'].read_group(domain=domain, fields=['product_id', 'product_qty'],
                                                                   groupby=['product_id'])
            for item in groups:
                product_qty += item['product_qty']
            template.invoice_count = -1 * product_qty

    @api.multi
    def action_view_invoice(self):

        action = self.env.ref('account.action_account_invoice_report_all').read()[0]
        products = self.env['product.product']
        for template in self:
            products |= template.product_variant_ids
        action[
            'context'] = "{ 'group_by':['type'], 'measures': ['product_qty', 'price_average'], 'col_group_by': ['date:year']  }"
        action['domain'] = "[('product_id','in',[" + ','.join(map(str, products.ids)) + "])]"
        return action
