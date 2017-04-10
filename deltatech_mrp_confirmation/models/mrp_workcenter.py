# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    partial_conf = fields.Boolean(string='Partial confirmation', defalut=False)
    worker_ids = fields.One2many('mrp.workcenter.worker', 'workcenter_id', string='Workers')


class MrpWorkcenterWorkers(models.Model):
    _name = 'mrp.workcenter.worker'
    _description = 'Work Center Worker'
    _order = "to_date DESC"

    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', required=True)
    worker_id = fields.Many2one('res.partner', string="Worker", domain=[('is_company','=',False)])
    from_date = fields.Date(string="Form Date", default=lambda *a: fields.Date.today())
    to_date = fields.Date(string="To Date", default='2999-12-31')


    #todo: de verificat daca un muncitor se gaseste  in doua inregistrari care au intervalele suprapuse

