# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details
 


from odoo import models, fields, api, _

from datetime import datetime, timedelta, date

class hr_attendance(models.Model):
    _inherit = "hr.attendance"

    for_date = fields.Datetime(string='For Date', compute="_compute_for_date", store=True)
    #type_contract = fields.Selection([('acord','Acord'),('regie','Regie')], default='')
    
    @api.multi
    @api.depends('check_in')
    def _compute_for_date(self):
        day_start = self.env['ir.config_parameter'].sudo().get_param('attendance.day_start', 7)
        day_start = int(day_start)
        # caclul ora de inceput zi lucratoare
        for attendance in self:

            for_date = fields.Datetime.from_string(attendance.check_in) - timedelta(hours=day_start)
            attendance.for_date = fields.Datetime.to_string(for_date)

"""
Ziua
Nume
Marca
Intrare
Iesire
Ore regie
Ore acord
Ore invoiri
Ore CO
Ore CM
Ore suplimentare
Ore CFS
Ore nemotivate
Ore Obligatii
Ore delegatii
										

"""