# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _


class MrpOrderGroup(models.TransientModel):
    _name = 'mrp.order.group'
    _description = "MRP Production Order Group"

    group_id = fields.Many2one('procurement.group', string="Procurement Group")
    date_planned = fields.Datetime(related="group_id.date_planned")
    production_ids = fields.Many2many('mrp.production', string='Production Order')

    @api.model
    def default_get(self, fields_list):
        defaults = super(MrpOrderGroup, self).default_get(fields_list)

        active_ids = self.env.context.get('active_ids', False)

        domain = [('id', 'in', active_ids), ('state', 'not in', ['done', 'cancel'])]
        group_ids = self.env['procurement.group']
        res = self.env['mrp.production'].search(domain)
        for production in res:
            group_ids |= production.procurement_group_id
        defaults['production_ids'] = [(6, 0, [rec.id for rec in res])]
        if len(group_ids) == 1:
            defaults['group_id'] = group_ids.id
        return defaults

    @api.multi
    def do_group(self):

        if not self.production_ids:
            return

        if not self.group_id:
            self.group_id.self.env["procurement.group"].create({})

        # trebuie sa caut toate aceste grupuri si sa le schimb?
        group_ids = self.env['procurement.group']
        for production in self.production_ids:
            group_ids |= production.procurement_group_id

        '''
        move_ids = self.env['stock.move'].search([('group_id', 'in', group_ids.ids),
                                                  ('production_id', 'in', self.production_ids.ids)])
        move_ids.write({'group_id': self.group_id.id})
        '''

        move_ids = self.env['stock.move'].search([('group_id', 'in', group_ids.ids),
                                                  ('raw_material_production_id', 'in', self.production_ids.ids)])
        move_ids.write({'group_id': self.group_id.id})
        for move in move_ids:
            #move.procurement_id.write({'group_id': self.group_id.id})
            move.picking_id.write({'group_id': self.group_id.id})

        '''
        pickings = self.env['stock.picking'].search([('group_id', 'in', group_ids.ids)])
        pickings.write({'group_id': self.group_id.id})
        '''

        '''
        procurement_orders = self.env["procurement.order"].search([('group_id', 'in', group_ids.ids)])
        procurement_orders.write({'group_id': self.group_id.id})
        '''

        self.production_ids.write({'procurement_group_id': self.group_id.id})
        return
