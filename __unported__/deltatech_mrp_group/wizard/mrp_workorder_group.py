# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _


class MrpWorkOrderGroup(models.TransientModel):
    _name = 'mrp.workorder.group'
    _description = "MRP Work Order Group"

    group_id = fields.Many2one('procurement.group', string="Procurement Group")
    date_planned = fields.Datetime(related="group_id.date_planned")
    workorder_ids = fields.Many2many('mrp.workorder', string='Production Order')

    @api.model
    def default_get(self, fields_list):
        defaults = super(MrpWorkOrderGroup, self).default_get(fields_list)

        active_ids = self.env.context.get('active_ids', False)

        domain = [('id', 'in', active_ids), ('state', 'not in', ['done', 'cancel'])]
        group_ids = self.env['procurement.group']
        res = self.env['mrp.workorder'].search(domain)
        for workorder in res:
            group_ids |= workorder.procurement_group_id
        defaults['workorder_ids'] = [(6, 0, [rec.id for rec in res])]
        if len(group_ids) == 1:
            defaults['group_id'] = group_ids.id
        return defaults

    @api.multi
    def do_group(self):

        if not self.workorder_ids:
            return

        if not self.group_id:
            name = self.env['ir.sequence'].next_by_code('mrp.consolidation')
            self.group_id.self.env["procurement.group"].create({'name': name})

        self.workorder_ids.write({'procurement_group_id': self.group_id.id})
        return
