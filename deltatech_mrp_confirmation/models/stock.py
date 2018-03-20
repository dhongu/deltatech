# coding=utf-8


from odoo import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def show_production(self):
        self.ensure_one()

        route_buy = self.env.ref('purchase.route_warehouse0_buy')
        route_manufacture = self.env.ref('mrp.route_warehouse0_manufacture')

        if route_manufacture.id in self.product_id.route_ids.ids:

            domain = [('state', 'not in', ['done', 'cancel']), ('product_id', '=', self.product_id.id)]
            production_ids = self.env['mrp.production'].search(domain)
            if not production_ids:
                return

            action = self.env.ref('mrp.mrp_production_action').read()[0]
            action['domain'] = "[('id','in', " + str(production_ids.ids) + ")]"
            return action

        if route_buy.id in self.product_id.route_ids.ids:
            domain = [('state', 'in', ['draft']), ('product_id', '=', self.product_id.id)]
            purchase_line = self.env['purchase.order.line'].search(domain)
            purchase_ids = self.env['purchase.order']
            for line in purchase_line:
                purchase_ids |= line.order_id

            if not purchase_ids:
                return

            action = self.env.ref('purchase.purchase_rfq').read()[0]
            action['domain'] = "[('id','in', " + str(purchase_ids.ids) + ")]"
            return action




