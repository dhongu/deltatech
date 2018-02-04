# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import base64

from PIL import Image

# worker_module = 'res.partner'
worker_module = 'hr.employee'


class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'



    code = fields.Char(string="Code", index=True, related='operation_id.code', readonly=True)
    procurement_group_id = fields.Many2one('procurement.group', 'Procurement Group',
                                              related='production_id.procurement_group_id')


    barcode_image = fields.Binary(string='Barcode Image', compute="_compute_barcode_image")
    qty_rework = fields.Float('Rework Quantity', states={'done': [('readonly', True)], 'cancel': [('readonly', True)]})
    qty_ready_prod = fields.Float('Quantity Ready for Production', compute="_compute_prev_work_order")
    prev_work_order_id = fields.Many2one('mrp.workorder', "Previous Work Order", compute="_compute_prev_work_order")

    @api.depends('state')
    def _compute_prev_work_order(self):
        for work_order in self:
            prev_work_order = self.search([('next_work_order_id', '=', work_order.id)], limit=1)
            work_order.prev_work_order_id = prev_work_order
            product_qty = work_order.production_id.product_qty
            if prev_work_order:
                work_order.qty_ready_prod = prev_work_order.qty_produced - prev_work_order.qty_rework
            else:
                work_order.qty_ready_prod = product_qty


    def _compute_barcode_image(self):
        for workorder in self:
            if workorder.code:
                barcode_image = self.env['report'].barcode('Code128', workorder.code, width=600, height=200,
                                                           humanreadable=0)

                image_stream = StringIO.StringIO(barcode_image)
                img = Image.open(image_stream)

                img = img.convert('RGBA')
                pixdata = img.load()
                width, height = img.size
                for y in xrange(height):
                    for x in xrange(width):
                        if pixdata[x, y] == (255, 255, 255, 255):
                            pixdata[x, y] = (255, 255, 255, 0)

                img = img.rotate(90, expand=True)
                image_stream = StringIO.StringIO()
                img.save(image_stream, 'PNG')
                barcode_image = image_stream.getvalue().encode('base64')
                workorder.barcode_image = barcode_image

    @api.multi
    def record_production(self):
        if (self.qty_producing + self.qty_produced) > self.qty_ready_prod:
            raise ValidationError(_('It is not possible to produce more that %s') % self.qty_ready_prod)
        res = super(MrpWorkorder, self).record_production()

        # se verifica daca se poate inchide comanda
        if self.production_id.check_to_done:
            self.production_id.button_mark_done()

        return res

    @api.multi
    def button_start(self):
        if  self.production_availability != 'assigned' and not self.workcenter_id.start_without_stock:
            raise ValidationError(_('It is not possible to start work without materials'))
        return super(MrpWorkorder, self).button_start()

class MrpWorkcenterProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"

    worker_id = fields.Many2one(worker_module, string="Worker", domain="[('id', 'in', possible_worker_ids[0][2])]")
    possible_worker_ids = fields.Many2many(worker_module, compute='_get_possible_worker_ids', readonly=True)

    qty_produced = fields.Float('Quantity', readonly=True)

    @api.one
    def _get_possible_worker_ids(self):
        workers = self.env[worker_module]

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
