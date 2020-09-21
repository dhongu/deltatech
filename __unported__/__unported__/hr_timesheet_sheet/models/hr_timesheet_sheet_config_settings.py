# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_project_timesheet_synchro = fields.Boolean(string="Timesheet app for Chrome/Android/iOS")
    timesheet_range = fields.Selection(related='company_id.timesheet_range', string="Timesheet range *")
