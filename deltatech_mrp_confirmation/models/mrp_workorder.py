# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    code = fields.Char(string="Code", index=True, related='operation_id.code', readonly=True)

class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    worker_id = fields.Many2one('res.partner', string="Worker", domain="[('id', 'in', possible_worker_ids[0][2])]")
    possible_worker_ids = fields.Many2many('res.partner', compute='_get_possible_worker_ids', readonly=True)

    qty_produced = fields.Float('Quantity', readonly=True)

    @api.one
    def _get_possible_worker_ids(self):
        workers = self.env['res.partner']
        for worker in self.workcenter_id.worker_ids:
            if worker.from_date <= fields.Date.today() <= worker.to_date:
                workers |= worker.worker_id
        self.possible_worker_ids = workers


    @api.multi
    def action_start_working(self):
        super(MrpWorkcenterProductivity, self).action_start_working()
        for work in self:
            if not work.worker_id:
                if len(work.possible_worker_ids) == 1:
                    worker_id = work.possible_worker_ids[0]
                    work.write({'worker_id': worker_id.id})
        return True