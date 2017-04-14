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


class mrp_production_conf(models.TransientModel):
    _name = 'mrp.production.conf'
    _description = "Production Confirmation"
    _inherit = ['barcodes.barcode_events_mixin']

    date = fields.Date(string="Execution date", default=fields.Date.today)

    production_id = fields.Many2one('mrp.production', string='Production Order',
                                    domain=[('state', 'in', ['planned', 'progress'])])
    product_id = fields.Many2one('product.product', 'Product', related='production_id.product_id', readonly=True)
    worker_id = fields.Many2one('res.partner', string="Worker", domain=[('is_company', '=', False)])

    code = fields.Char('Operation Code')
    operation_id = fields.Many2one('mrp.workorder', string="Operation")

    qty_production = fields.Float('Original Production Quantity', readonly=True, related='production_id.product_qty')
    qty_produced = fields.Float('Quantity', readonly=True, related='operation_id.qty_produced')
    qty_producing = fields.Float('Currently Produced Quantity', related='operation_id.qty_producing')

    operation_ids = fields.Many2many('mrp.workorder', string="Operations", readonly=True)

    error_message = fields.Char(string="Error Message", readonly=True)
    success_message = fields.Char(string="Success Message", readonly=True)
    info_message = fields.Char(string="Info Message", readonly=True)

    @api.onchange('production_id', 'code')
    def onchange_production_id(self):

        operation_domain = [('state', 'not in', ['done', 'cancel'])]
        if self.production_id:
            operation_domain += [('production_id', '=', self.production_id.id)]

        if self.code:
            operation_domain += [('code', '=', self.code)]

        operation_ids = self.env['mrp.workorder'].search(operation_domain)

        if operation_ids:
            # daca operatia selectata nu este in lista de operatii a comenzii atunci trebuire reselectata
            if self.operation_id and self.operation_id.id not in operation_ids.ids:
                self.operation_id = False

            """
            # daca pana in acest punct nu am aveut o operatie sau nu am determinat una atunci o aleg pe prima
            if not self.operation_id and operation_ids:
                self.operation_id = operation_ids[0]
            """

        self.operation_ids = operation_ids

        return {
            'domain': {'operation_id': [('id', 'in', operation_ids.ids)]}
        }

    @api.onchange('operation_id')
    def onchange_operation_id(self):
        if self.operation_id and self.operation_id.workcenter_id.partial_conf:
            self.qty_producing = 1.0
        self.code = self.operation_id.code
        workers = self.get_workers(self.operation_id)
        if self.worker_id and self.worker_id not in workers:
            self.worker_id = False
        if len(workers) == 1:
            self.worker_id = workers[0]
        if workers:
            worker_domain = [('id', 'in', workers.ids)]
        else:
            worker_domain = [('is_company', '=', False)]
        return {
            'domain': {'worker_id': worker_domain}
        }

    @api.onchange('worker_id')
    def onchange_worker_id(self):
        if self.worker_id and self.operation_id:
            if self.worker_id not in self.get_workers(self.operation_id):
                self.error_message = _('Worker %s not assigned to work center %s') % (
                    self.worker_id.name, self.operation_id.workcenter_id.name)
                self.worker_id = False

    def get_workers(self, operation_id):
        workers = self.env['res.partner']
        for worker in operation_id.workcenter_id.worker_ids:
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

        #self.success_message = False

        production = self.production_id
        operation = self.operation_id
        code = self.code
        worker = self.worker_id
        confirm_message = ''

        nomenclature = self.env['barcode.nomenclature'].search([], limit=1)
        if nomenclature:
            scann = nomenclature.parse_barcode(barcode)

            if scann['type'] == 'error':
                self.error_message = _('Invalid bar code %s') % barcode
                return

            if scann['type'] == 'mrp_order':
                domain = [('name', '=', scann['code']), ('state', 'in', ['planned', 'progress'])]
                production = self.env['mrp.production'].search(domain)
                if not production:
                    self.error_message = _('Production Order %s not found') % barcode
                else:
                    self.info_message = _('Production Order %s was scanned.') % production.name
                # a fost rescanata comadna
                if production == self.production_id:
                    if self.operation_id and self.operation_id.workcenter_id.partial_conf:
                        self.qty_producing += 1
                        self.info_message = _('Incremented quantity')
                        return

            if scann['type'] == 'mrp_operation':
                if scann['code'] == self.code:
                    if self.operation_id and self.operation_id.workcenter_id.partial_conf:
                        self.qty_producing += 1
                        self.info_message = _('Incremented quantity')
                        return

                code = scann['code']

                if production:
                    operation_domain = [('production_id', '=', production.id),
                                        ('code', '=', code),
                                        ('state', 'not in', ['done', 'cancel'])]
                else:
                    operation_domain = [('code', '=', code), ('state', 'not in', ['done', 'cancel'])]

                operation = self.env['mrp.workorder'].search(operation_domain, limit=1)
                if not operation:
                    self.error_message = _('Operation with code %s not found') % code
                    code = False
                else:
                    self.info_message = _('Operation %s was scanned') % operation.name

            if scann['type'] == 'mrp_worker':
                domain = [('ref', '=', scann['code'])]
                worker = self.env['res.partner'].search(domain, limit=1)
                if not worker:
                    self.error_message = _('Worker %s not found') % barcode
                else:
                    self.info_message = _('Worker %s was scanned') % worker.name
                    if worker not in  self.get_workers(operation):
                        self.error_message = _('Worker %s not assigned to work center %s') % (
                            worker.name, operation.workcenter_id.name)


        if self.production_id and self.operation_id and self.worker_id:
            if production != self.production_id or self.operation_id != operation or self.worker_id != worker:
                self.success_message = _('Confirm saved for operation %s') % self.operation_id.name

                self.confirm(operation=self.operation_id, worker=self.worker_id, qty_producing=self.qty_producing)

        self.production_id = production
        self.code = code
        self.operation_id = operation
        self.worker_id = worker

        if self.production_id and self.operation_id and self.worker_id:
            self.info_message = _('System is ready for confirmation order %s operation %s with %s') % (
                production.name, operation.name, worker.name)



        return

    @api.model
    def confirm(self, operation, worker, qty_producing):

        if operation.state in ['pending', 'ready']:
            operation.button_start()

        operation.qty_producing = qty_producing  # de ce nu merge la onchange ????
        # Update workorder quantity produced
        # operation.qty_produced += qty_producing


        time_ids = operation.time_ids.filtered(lambda x: (x.user_id.id == self.env.user.id) and
                                                         (not x.date_end) and (
                                                             x.loss_type in ('productive', 'performance')))
        if time_ids:
            time_ids.write({'worker_id': worker.id, 'qty_produced': qty_producing})

        operation.record_production()
        operation.end_previous()
        if operation.state == 'progress':  # daca nu a fost finalizata comanda
            operation.button_start()
        if operation.production_id.check_to_done:
            operation.production_id.button_mark_done()

        operation.write({'qty_producing': operation.qty_producing,
                         'qty_produced': operation.qty_produced})



    @api.model
    def default_get(self, fields):
        defaults = super(mrp_production_conf, self).default_get(fields)

        active_id = self.env.context.get('active_id', False)
        if active_id:
            defaults['production_id'] = active_id
        return defaults

    @api.multi
    def do_confirm(self):
        if self.production_id and self.operation_id and self.worker_id:
            self.confirm(operation=self.operation_id, worker=self.worker_id, qty_producing=self.qty_producing)
        action = self.env.ref('deltatech_mrp_confirmation.action_mrp_production_conf').read()[0]
        # action['context'] = {'default_production_id':self.production_id.id,
        #                     'default_code': self.code}
        self.write({'production_id': self.production_id.id})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mrp.production.conf',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
