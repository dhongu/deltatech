# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _


class SaleOrderGroup(models.TransientModel):
    _name = 'sale.order.group'
    _description = "Sele Order Group"

    group_id = fields.Many2one('procurement.group', string="Procurement Group")
    sale_order_ids = fields.Many2many('sale.order', string='Production Order')
    date_planned = fields.Datetime(related="group_id.date_planned")



    @api.model
    def default_get(self, fields_list):
        defaults = super(SaleOrderGroup, self).default_get(fields_list)

        active_ids = self.env.context.get('active_ids', False)

        domain = [('id', 'in', active_ids), ('state', 'not in', ['done', 'cancel'])]
        res = self.env['sale.order'].search(domain)

        group_ids = self.env['procurement.group']
        for order in res:
            group_ids |= order.procurement_group_id
        if len(group_ids) == 1:
            defaults['group_id'] = group_ids.id

        defaults['sale_order_ids'] = [(6, 0, [rec.id for rec in res])]
        return defaults



    @api.multi
    def do_group(self):
        if not self.sale_order_ids:
            return

        if not self.group_id:
            self.group_id = self.env["procurement.group"].create({})

        # trebuie sa caut toate aceste grupuri si sa le schimb?
        group_ids = self.env['procurement.group']
        for order in self.sale_order_ids:
            group_ids |= order.procurement_group_id

        if group_ids:
            production_ids = self.env['mrp.production'].search([('procurement_group_id', 'in', group_ids.ids)])
            production_ids.write({'group_id': self.group_id.id})

            move_ids = self.env['stock.move'].search([('group_id', 'in', group_ids.ids)])
            move_ids.write({'group_id': self.group_id.id})

            # procurement_orders = self.env["procurement.order"].search([('group_id', 'in', group_ids.ids)])
            # procurement_orders.write({'group_id': self.group_id.id})

            pickings = self.env['stock.picking'].search([('group_id', 'in', group_ids.ids)])
            pickings.write({'group_id': self.group_id.id})

        self.sale_order_ids.write({'procurement_group_id': self.group_id.id})
        return
