# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
#                    Dorin Hongu <dhongu(@)gmail(.)com       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _

# worker_module = 'res.partner'
worker_module = 'hr.employee'


class mrp_production_conf(models.TransientModel):
    _name = 'mrp.production.conf'
    _description = "Production Confirmation"
    _inherit = ['barcodes.barcode_events_mixin']

    date_start = fields.Datetime('Start Date', required=True, default=fields.Datetime.now)
    date_end = fields.Datetime('End Date', required=True, default=fields.Datetime.now)
    duration = fields.Float('Duration', store=True)  # compute='_compute_duration',

    production_id = fields.Many2one('mrp.production', string='Production Order',
                                    domain=[('state', 'in', ['planned', 'progress'])])

    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group',
                                              related='production_id.procurement_group_id')

    product_id = fields.Many2one('product.product', 'Product', related='production_id.product_id', readonly=True)
    # worker_id = fields.Many2one('res.partner', string="Worker", domain=[('is_company', '=', False)])
    worker_id = fields.Many2one(worker_module, string="Worker")

    has_tracking = fields.Selection(related='product_id.tracking', string='Product with Tracking')
    lot_id = fields.Many2one('stock.production.lot', string="Lot / Serial Number")

    code = fields.Char('Operation Code')
    workorder_id = fields.Many2one('mrp.workorder', string="Workorder",
                                   domain="[('state', 'not in', ['done', 'cancel']), ('production_id','=',production_id) ]")

    qty_production = fields.Float('Original Production Quantity', readonly=True,
                                  related = 'production_id.product_qty' )

    qty_ready_prod = fields.Float('Quantity Ready for Production', readonly=True,
                                  related = 'workorder_id.qty_ready_prod' )

    qty_produced = fields.Float('Quantity', readonly=True, related='workorder_id.qty_produced')
    qty_producing = fields.Float('Currently Produced Quantity', related='workorder_id.qty_producing')

    workorder_ids = fields.Many2many('mrp.workorder', string="Workorders", readonly=True)

    error_message = fields.Char(string="Error Message", readonly=True)
    success_message = fields.Char(string="Success Message", readonly=True)
    info_message = fields.Char(string="Info Message", readonly=True)




    """
    @api.depends('workorder_id', 'qty_producing','date_end','date_start')
    def _compute_duration(self):
        workorder = self.workorder_id
        if not workorder.workcenter_id.confirm_real_time:
            if workorder.workcenter_id.time_efficiency:
                self.duration = (workorder.workcenter_id.time_start + workorder.workcenter_id.time_stop +
                                 self.qty_producing * workorder.operation_id.time_cycle * 100.0 / workorder.workcenter_id.time_efficiency)
            else:
                self.duration = 0.0
        else:
            if self.date_end:
                diff = fields.Datetime.from_string(self.date_end) - fields.Datetime.from_string(self.date_start)
                self.duration = round(diff.total_seconds() / 60.0, 2)
            else:
                self.duration = 0.0

    @api.onchange('date_end')
    def onchange_date_end(self):
        if self.date_end:
            self.date_start = fields.Datetime.to_string(fields.Datetime.from_string(self.date_end) -
                                                        timedelta(minutes=self.duration))

    @api.onchange('date_start')
    def onchange_date_start(self):
        if self.date_start:
            self.date_end = fields.Datetime.to_string(fields.Datetime.from_string(self.date_start) +
                                                      timedelta(minutes=self.duration))
    """

    @api.onchange('production_id')
    def onchange_production_id(self):

        workorder_domain = [('state', 'not in', ['done', 'cancel'])]
        if self.production_id:
            workorder_domain += [('production_id', '=', self.production_id.id)]

        # if self.code:
        #    workorder_domain += [('code', '=', self.code)]

        workorder_ids = self.env['mrp.workorder'].search(workorder_domain)

        if workorder_ids:
            # daca operatia selectata nu este in lista de operatii a comenzii atunci trebuire reselectata
            if self.workorder_id and self.workorder_id.id not in workorder_ids.ids:
                self.workorder_id = False

            """
            # daca pana in acest punct nu am aveut o operatie sau nu am determinat una atunci o aleg pe prima
            if not self.workorder_id and workorder_ids:
                self.workorder_id = workorder_ids[0]
            """

        self.workorder_ids = workorder_ids

        return {
            'domain': {'workorder_id': [('id', 'in', workorder_ids.ids)]}
        }

    @api.onchange('workorder_id')
    def onchange_workorder_id(self):
        if self.workorder_id and self.workorder_id.workcenter_id.partial_conf:
            self.qty_producing = 1.0
        # self.code = self.workorder_id.code
        self.date_start = self.workorder_id.date_planned_start or self.production_id.date_planned_start or fields.Datetime.now()
        self.date_end = self.workorder_id.date_planned_finished or self.production_id.date_planned_finished or fields.Datetime.now()
        self.duration = self.workorder_id.duration_expected or 0.0
        workers = self.get_workers(self.workorder_id, self.worker_id)
        if self.worker_id and self.worker_id not in workers:
            self.worker_id = False
        if len(workers) == 1:
            self.worker_id = workers[0]
        if workers:
            worker_domain = [('id', 'in', workers.ids)]
        else:
            if worker_module == 'res.partner':
                worker_domain = [('is_company', '=', False)]
            else:
                worker_domain = []
        return {
            'domain': {'worker_id': worker_domain}
        }

    @api.onchange('worker_id')
    def onchange_worker_id(self):
        if self.worker_id and self.workorder_id:
            if self.worker_id not in self.get_workers(self.workorder_id, self.worker_id):
                self.error_message = _('Worker %s not assigned to work center %s') % (
                    self.worker_id.name, self.workorder_id.workcenter_id.name)
                self.worker_id = False

    @api.onchange('qty_producing')
    def onchange_qty_producing(self):
        if ( self.qty_producing + self.qty_produced ) > self.qty_ready_prod:
            self.qty_producing = self.qty_ready_prod - self.qty_produced

    def get_workers(self, workorder_id, worker=False):
        workers = self.env[worker_module]
        if not workorder_id.workcenter_id.worker_ids:
            return worker
        for worker in workorder_id.workcenter_id.worker_ids:
            if worker.from_date <= fields.Date.today() <= worker.to_date:
                workers |= worker.worker_id
        return workers

    def search_scanned(self, barcode):
        self.on_barcode_scanned(barcode)
        action = {}
        if self.error_message:
            action = {
                'warning': {'title': "Warning", 'message': self.error_message},
            }
        return action

    def on_barcode_scanned(self, barcode):
        self.error_message = False
        self.success_message = False
        self.info_message = False

        # self.success_message = False

        production = self.production_id
        workorder = self.workorder_id
        # code = self.code
        worker = self.worker_id
        lot = self.lot_id
        confirm_message = ''

        if barcode != '#save':
            nomenclature = self.env['barcode.nomenclature'].search([], limit=1)
            if nomenclature:
                scann = nomenclature.parse_barcode(barcode)

                if scann['type'] == 'error':
                    self.error_message = _('Invalid bar code %s') % barcode
                    return
                if scann['type'] == 'lot':
                    domain = [('name', '=', scann['code'])]
                    lot = self.env['stock.production.lot'].search(domain)
                    if not lot:
                        self.error_message = _('Lot %s not found') % barcode
                    else:
                        self.info_message = _('Lot %s was scanned.') % production.name
                    if lot:
                        domain = [('lot_produced_id', '=', lot.id)]
                        move_lot = self.env['stock.move.lots'].search(domain)
                        if move_lot:
                            production = move_lot.production_id

                if scann['type'] == 'mrp_order':
                    domain = [('name', '=', scann['code']), ('state', 'in', ['planned', 'progress'])]
                    production = self.env['mrp.production'].search(domain)
                    if not production:
                        self.error_message = _('Production Order %s not found') % barcode
                    else:
                        self.info_message = _('Production Order %s was scanned.') % production.name
                    # a fost rescanata comadna
                    if production == self.production_id:
                        if self.workorder_id and self.workorder_id.workcenter_id.partial_conf:
                            self.qty_producing += 1
                            self.info_message = _('Incremented quantity')
                            if (self.qty_producing + self.qty_produced) > self.qty_ready_prod:
                                self.qty_producing = self.qty_ready_prod - self.qty_produced
                                self.info_message = ''
                                self.error_message = _('It is not possible to increase the quantity')
                            return
                    if self.code and not workorder:
                        workorder_domain = [('production_id', '=', production.id),
                                            ('code', '=', self.code),
                                            ('state', 'not in', [  'cancel'])]

                        workorder = self.env['mrp.workorder'].search(workorder_domain, limit=1)
                        if not workorder:
                            self.error_message = _('Operation with code %s not found') % self.code
                            workorder = False


                if scann['type'] == 'mrp_operation':
                    # nu trebuie facuta incrementarea de cantitate daca se rescanreaza codul operatiei
                    """
                    if scann['code'] == self.workorder_id.code:
                        if self.workorder_id.workcenter_id.partial_conf:
                            self.qty_producing += 1
                            self.info_message = _('Incremented quantity')
                            return
                    """
                    code = scann['code']
                    self.code = scann['code']


                    if production:
                        workorder_domain = [('production_id', '=', production.id),
                                            ('code', '=', code),
                                            ('state', 'not in', [ 'cancel'])]
                        workorder = self.env['mrp.workorder'].search(workorder_domain, limit=1)
                        if not workorder:
                            self.error_message = _('Operation with code %s not found') % code
                            workorder = False
                        else:
                            self.info_message = _('Operation %s was scanned') % workorder.name
                    else:
                        self.info_message = _('Operation %s was scanned') % code




                if scann['type'] == 'mrp_worker':
                    if worker_module == 'res.partner':
                        domain = [('ref', '=', scann['code'])]
                    if worker_module == 'hr.employee':
                        domain = [('barcode', '=', scann['code'])]

                    worker = self.env[worker_module].search(domain, limit=1)
                    if not worker:
                        self.error_message = _('Worker %s not found') % barcode
                    else:
                        self.info_message = _('Worker %s was scanned') % worker.name
                        if worker not in self.get_workers(workorder, worker):
                            self.error_message = _('Worker %s not assigned to work center %s') % (
                                worker.name, workorder.workcenter_id.name)




        if workorder and self.workorder_id != workorder and workorder.workcenter_id.partial_conf:
            if workorder.qty_produced < workorder.qty_ready_prod:
                self.qty_producing = 1.0
                workorder.qty_producing = 1.0
            else:
                self.qty_producing = 0.0
                workorder.qty_producing = 0.0

        if self.production_id and self.workorder_id and self.worker_id:
            if production != self.production_id or self.workorder_id != workorder or self.worker_id != worker or barcode == '#save':
                self.success_message = _('Confirm saved for operation %s') % self.workorder_id.name
                if self.qty_producing > 0:
                    self.confirm()  # workorder=self.workorder_id, worker=self.worker_id, qty_producing=self.qty_producing)

        self.production_id = production
        # self.code = code
        self.workorder_id = workorder
        self.worker_id = worker

        if self.production_id and self.workorder_id and self.worker_id and self.qty_producing > 0:
            self.info_message = _('System is ready for confirmation order %s operation %s with %s') % (
                production.name, workorder.name, worker.name)

        return

    @api.model
    def confirm(self):  # , workorder, worker, qty_producing):

        workorder = self.workorder_id
        worker = self.worker_id
        qty_producing = self.qty_producing

        if workorder.state in ['pending', 'ready']:
            workorder.button_start()

        workorder.qty_producing = qty_producing  # de ce nu merge la onchange ????

        if (self.qty_producing + self.qty_produced) > self.qty_ready_prod:
            raise Warning( _('It is not possible to increase the quantity'))




        time_ids = workorder.time_ids.filtered(lambda x: (x.user_id.id == self.env.user.id) and
                                                         (not x.date_end) and (
                                                             x.loss_type in ('productive', 'performance')))
        if time_ids:
            time_values = {'worker_id': worker.id,
                           'qty_produced': qty_producing,
                           'duration': self.duration,
                           'date_start': self.date_start,
                           'date_end': self.date_end,
                           }
            """
            if not workorder.workcenter_id.confirm_real_time:
                cycle_number = qty_producing  # math.ceil(qty_producing / workorder.workcenter_id.capacity)  # TODO: float_round UP
                duration_expected = (workorder.workcenter_id.time_start +
                                     workorder.workcenter_id.time_stop +
                                     cycle_number * workorder.operation_id.time_cycle * 100.0 / workorder.workcenter_id.time_efficiency)
                print duration_expected
                time_values['duration'] = duration_expected
            """
            time_ids.write(time_values)

        workorder.record_production()
        workorder.end_previous()
        if workorder.state == 'progress':  # daca nu a fost finalizata comanda
            workorder.button_start()


        workorder.write({'qty_producing': workorder.qty_producing,
                         'qty_produced': workorder.qty_produced})

        if workorder.state == 'done' and self.workorder_id.next_work_order_id:
            self.workorder_id = self.workorder_id.next_work_order_id
            self.date_start = self.workorder_id.date_planned_start or fields.Datetime.now()
            self.date_end = self.workorder_id.date_planned_finished or fields.Datetime.now()
            self.duration = self.workorder_id.duration_expected or 0.0
            return True

        if self.workorder_id.next_work_order_id:
            return False

    @api.model
    def default_get(self, fields):
        defaults = super(mrp_production_conf, self).default_get(fields)

        active_id = self.env.context.get('active_id', False)
        if active_id:
            defaults['production_id'] = active_id
        return defaults

    @api.multi
    def do_confirm(self):
        next = True
        if self.production_id and self.workorder_id and self.worker_id:
            next = self.confirm()  # workorder=self.workorder_id, worker=self.worker_id, qty_producing=self.qty_producing)
        action = self.env.ref('deltatech_mrp_confirmation.action_mrp_production_conf').read()[0]
        # action['context'] = {'default_production_id':self.production_id.id,
        #                     'default_code': self.code}
        values = {'production_id': self.production_id.id}
        if self.workorder_id.state == 'done':  # daca a fost facuta operatia nu mai trebuie afisata
            values['workorder_id'] = self.workorder_id.next_work_order_id.id
        self.write(values)
        if next:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mrp.production.conf',
                'view_mode': 'form',
                'view_type': 'form',
                'res_id': self.id,
                'views': [(False, 'form')],
                'target': 'new',
            }
