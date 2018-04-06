# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MrpRework(models.Model):
    _name = 'mrp.rework'
    _description = "Mrp rework"
    _inherit = 'mail.thread'

    name = fields.Char(string='Name', index=True, default='/', readonly=True,  copy=False)
    production_id = fields.Many2one('mrp.production', string='Manufacturing Order', index=True,
                                    ondelete='cascade', required=True,
                                    readonly=True, states={'draft': [('readonly', False)]})
    qty_rework = fields.Float(string="Quantity", readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Date('Date', default=lambda *a: fields.Date.today(),
                       readonly=True, states={'draft': [('readonly', False)]})
    order_ids = fields.Many2many('mrp.workorder', 'mrp_rework_order', 'rework_id', 'workorder_id', string="Orders",
                                 domain="[('production_id','=',production_id)]",
                                 readonly=True, states={'draft': [('readonly', False)]})

    state = fields.Selection([('draft', 'Draft'), ('posted', 'Posted')], string='Status', default='draft')

    @api.multi
    def action_posted(self):
        for rework in self:
            for order in rework.order_ids:
                order.write({'qty_rework': order.qty_rework + rework.qty_rework,
                             'qty_produced':order.qty_produced -  rework.qty_rework})
        return self.write({'state': 'posted'})

    @api.multi
    def action_draft(self):
        for rework in self:
            for order in rework.order_ids:
                order.write({'qty_rework': order.qty_rework - rework.qty_rework,
                             'qty_produced':order.qty_produced + rework.qty_rework})
        return self.write({'state': 'draft'})

    @api.model
    def create(self, vals):
        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            sequence_rework = self.env.ref('mrp.sequence_rework')
            if sequence_rework:
                vals['name'] = sequence_rework.next_by_id()
        return super(MrpRework, self).create(vals)
