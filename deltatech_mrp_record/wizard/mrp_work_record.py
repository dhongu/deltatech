# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import models, fields, api, _
from odoo.exceptions import UserError, RedirectWarning

# worker_module = 'res.partner'
worker_module = 'hr.employee'


class MrpWorkRecord(models.TransientModel):
    _name = 'mrp.work.record'
    _description = "MRP Record Production"
    _inherit = ['barcodes.barcode_events_mixin']

    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group')
    error_message = fields.Char(string="Error Message", readonly=True)
    success_message = fields.Char(string="Success Message", readonly=True)
    info_message = fields.Char(string="Info Message", readonly=True)

    @api.model
    def get_workers_ids(self, work_order_ids):
        productivity = self.env["mrp.workcenter.productivity"].search([('workorder_id', 'in', work_order_ids)])
        productivity = productivity.filtered(lambda x: x.date_end == False)

        workers = self.env[worker_module]
        for prod in productivity:
            workers |= prod.worker_id

        return workers

    @api.model
    def get_workers_name(self, work_order_ids):
        workers = self.get_workers_ids(work_order_ids)
        return workers.read(['id', 'name'])

    @api.model
    def search_scanned(self, barcode, values):
        action = self.on_barcode_scanned(barcode, values)
        if action['error_message']:
            action.update({
                'warning': {'title': "Warning", 'message': action['error_message']},
            })

        return action

    @api.model
    def on_barcode_scanned(self, barcode, old_values=None):
        if not old_values:
            values = {}
        else:
            values = dict(old_values)

        values.update({
            'error_message': False,
            'success_message': False,
            'info_message': False,
            'warning': False,
        })

        nomenclature = self.env['barcode.nomenclature'].search([], limit=1)
        if not nomenclature:
            values['error_message'] = _('Barcode nomenclature not found')
            return values

        scann = nomenclature.parse_barcode(barcode)

        values['scann'] = scann

        if scann['type'] == 'error':
            values['error_message'] = _('Invalid bar code %s') % barcode


        elif scann['type'] == 'mrp_worker':
            domain = []
            if worker_module == 'res.partner':
                domain = [('ref', '=', scann['code'])]
            if worker_module == 'hr.employee':
                domain = [('barcode', '=', scann['code'])]

            worker = self.env[worker_module].search(domain, limit=1)
            if not worker:
                values['error_message'] = _('Worker %s not found') % barcode
            else:
                values['info_message'] = _('Worker %s was scanned') % worker.name

                # se gaeste in comanda de lucru?
                if values['work_order_ids']:
                    loss_id = self.env['mrp.workcenter.productivity.loss'].search([('loss_type', '=', 'productive')],
                                                                                  limit=1)
                    time_ids = self.env["mrp.workcenter.productivity"].search(
                        [('workorder_id', 'in', values['work_order_ids'])])
                    time_ids = time_ids.filtered(lambda x: x.date_end == False and x.worker_id.id == worker.id)
                    if time_ids:
                        time_ids.write({'date_end': fields.Datetime.now()})
                    else:
                        work_orders = self.env['mrp.workorder'].browse(values['work_order_ids'])
                        for work_order in work_orders:
                            self.env["mrp.workcenter.productivity"].create({
                                'workorder_id': work_order.id,
                                'workcenter_id': work_order.workcenter_id.id,
                                'worker_id': worker.id,
                                'loss_id': loss_id.id,
                                'date_start': fields.Datetime.now()
                            })

        elif scann['type'] == 'mrp_operation':
            workorder_domain = [('code', '=', barcode),
                                ('state', 'in', ['planned', 'progress'])]
            work_orders = self.env['mrp.workorder'].search(workorder_domain)
            if not work_orders:
                values['error_message'] = _('For the operation code %s there are no work order') % barcode
            else:
                values['work_order_ids'] = work_orders.ids


        elif scann['type'] == 'mrp_group':
            domain = [('name', '=', scann['code'])]
            procurement_group = self.env['procurement.group'].search(domain, limit=1)
            if not procurement_group:
                values['error_message'] = _('Work order group %s not found') % barcode
            else:
                values['info_message'] = _('Work order %s was scanned') % procurement_group.name
                values['procurement_group_id'] = procurement_group.id
                work_orders = self.env['mrp.workorder'].search([('procurement_group_id', '=', procurement_group.id),
                                                                ('state', 'in', ['planned', 'progress'])])
                if not work_orders:
                    values['error_message'] = _('For the group %s there are no work order') % barcode
                else:
                    values['work_order_ids'] = work_orders.ids
        else:
            values['error_message'] = _('The type %s is not used in this screen') % (scann['type'])

        return values
