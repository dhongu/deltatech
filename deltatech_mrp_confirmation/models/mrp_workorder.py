# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

import base64

from PIL import Image


#worker_module = 'res.partner'
worker_module = 'hr.employee'

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    code = fields.Char(string="Code", index=True, related='operation_id.code', readonly=True)

    barcode_image = fields.Binary(string='Barcode Image', compute="_compute_barcode_image")


    def _compute_barcode_image(self):
        for workorder in self:
            if workorder.code:
                barcode_image = self.env['report'].barcode('Code128', workorder.code, width=600, height=200,  humanreadable=0)

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