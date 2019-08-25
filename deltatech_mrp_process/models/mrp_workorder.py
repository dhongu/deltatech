# -*- coding: utf-8 -*-
# ©  2015-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, _, api


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    location_dest_id = fields.Many2one('stock.location', related='production_id.location_dest_id',
                                       string='Tank', readonly=False)

    # todo: de investigat de ce nu se salveaza locatia dest pentru ca e un camp related si a trebuit sa-l pun in write

    @api.multi
    def write(self, vals):
        if 'location_dest_id' in vals:
            for workorder in self:
                workorder.production_id.write({'location_dest_id': vals['location_dest_id']})

        return super(MrpWorkorder, self).write(vals)

    @api.onchange('qty_producing')
    def _onchange_qty_producing(self):
        if self.state == 'ready':
            return super(MrpWorkorder, self)._onchange_qty_producing()

    @api.multi
    def button_finish(self):
        super(MrpWorkorder, self).button_finish()
        for workorder in self:
            if workorder.next_work_order_id:
                values = {'qty_producing': workorder.qty_produced}
                if workorder.next_work_order_id.state == 'pending':
                    values['state'] = 'ready'
                workorder.next_work_order_id.write(values)

    @api.multi
    def button_next(self):
        if self.next_work_order_id:
            # action = self.env.ref('mrp.action_work_orders').read()[0]

            action = {
                'name': _('Work Order'),
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.workorder',
                'target': 'main',
                'views': [[self.env.ref('mrp.mrp_production_workorder_form_view_inherit').id, 'form']],
                'res_id': self.next_work_order_id.id
            }


        else:
            action = {
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.production',
                'views': [[self.env.ref('mrp.mrp_production_form_view').id, 'form']],
                'res_id': self.production_id.id,
                'target': 'main',
                'flags': {
                    'headless': False,
                }
            }
        return action

    @api.multi
    def button_done_finish(self):
        self.record_production()
        for workorder in self:
            if workorder.state == 'progress':
                self.button_finish()
                workorder.active_move_line_ids.unlink()

    @api.multi
    def record_production(self):
        super(MrpWorkorder, self).record_production()

    def _generate_lot_ids(self):
        """ Generate stock move lines """
        super(MrpWorkorder, self)._generate_lot_ids()

        move_lines = self.active_move_line_ids
        for move_line in move_lines:
            line = move_line.move_id.move_line_ids.filtered(lambda line: line.lot_id != False and line.product_id == move_line.product_id)
            if line:
                line = line[0]
                move_line.write({'lot_id': line.lot_id.id})
