# coding=utf-8


from odoo import models, fields, api, _

class ProcurementGroup(models.Model):
    _inherit = 'procurement.group'

    date_planned = fields.Datetime('Scheduled Date', default=fields.Datetime.now,
        required=True, index=True, track_visibility='onchange')