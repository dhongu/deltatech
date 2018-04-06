# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.multi
    def show_production(self):
        self.ensure_one()

        route_buy = self.env.ref('purchase.route_warehouse0_buy')
        route_manufacture = self.env.ref('mrp.route_warehouse0_manufacture')
        rule_action = []
        for route in self.product_id.route_ids:
            for rule in route.pull_ids:
                rule_action += [rule.action]

        #if route_manufacture.id in self.product_id.route_ids.ids:
        if 'manufacture' in rule_action:
            domain = [('state', 'not in', ['done', 'cancel']), ('product_id', '=', self.product_id.id)]
            production_ids = self.env['mrp.production'].search(domain)
            if  production_ids:
                action = self.env.ref('mrp.mrp_production_action').read()[0]
                action['domain'] = "[('id','in', " + str(production_ids.ids) + ")]"
                return action

        #if route_buy.id in self.product_id.route_ids.ids:
        if 'buy' in rule_action:
            domain = [('state', 'in', ['draft']), ('product_id', '=', self.product_id.id)]
            purchase_line = self.env['purchase.order.line'].search(domain)
            purchase_ids = self.env['purchase.order']
            for line in purchase_line:
                purchase_ids |= line.order_id

            if purchase_ids:
                action = self.env.ref('purchase.purchase_rfq').read()[0]
                action['domain'] = "[('id','in', " + str(purchase_ids.ids) + ")]"
                return action




