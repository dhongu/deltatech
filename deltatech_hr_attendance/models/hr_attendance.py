# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
# See README.rst file on addons root folder for license details


from odoo import models, fields, api, _
import pytz
from datetime import datetime, timedelta, date


def utc_to_local(event_time):
    tz_name = "Europe/Bucharest"
    tz = pytz.timezone(tz_name)

    event_time = pytz.UTC.localize(event_time).astimezone(tz).replace(tzinfo=None)

    return event_time


class hr_attendance(models.Model):
    _inherit = "hr.attendance"

    for_date = fields.Date(string='For Date', compute="_compute_for_date", store=True, readonly=False)
    no_check_out = fields.Boolean()
    state = fields.Selection([('ok','OK'),('no_in','No check in'),('no_out','No check'),('manual','Manual')], default='ok')


    @api.multi
    @api.depends('check_in', 'check_out')
    def _compute_for_date(self):
        day_start = self.env['ir.config_parameter'].sudo().get_param('attendance.day_start', 6)
        day_start = int(day_start)
        # caclul ora de inceput zi lucratoare
        for attendance in self:
            date_time_in = fields.Datetime.from_string(attendance.check_in) - timedelta(hours=day_start)
            date_time_in = utc_to_local(date_time_in)
            date_in = fields.Date.to_string(date_time_in)
            attendance.for_date = date_in
            if attendance.check_out:
                date_time_out = fields.Datetime.from_string(attendance.check_out) - timedelta(hours=day_start)
                date_time_out = utc_to_local(date_time_out)
                date_out = fields.Date.to_string(date_time_out)
                if date_in != date_out:
                    date_time_00 = fields.Datetime.from_string(date_out + ' 00:00:00')
                    d1 = date_time_00 - date_time_in
                    d2 = date_time_out - date_time_00
                    if d2 > d1:
                        attendance.for_date = date_out


