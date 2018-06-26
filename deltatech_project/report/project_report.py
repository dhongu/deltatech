# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2014 Deltatech All Rights Reserved
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


import time
import datetime

from odoo import api, models


class ReportProjectAbstract(models.AbstractModel):
    _name = 'report.abstract_report.project'
    _template = None

    @api.model
    def get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report']._get_report_from_name(self._template)
        return {
            'doc_ids': docids,
            'doc_model': report.model,
            'data': data,
            'time': time,
            'docs': self.env[report.model].browse(docids),
            'formatLang': self._formatLang,
            'get_line': self._get_line,
            'get_totals': self._get_totals,
            'reduce': reduce,

            'datetime': datetime,
            'today': time.strftime('%Y-%m-%d'),
            'tomorrow': datetime.datetime.strftime(datetime.date.today() + datetime.timedelta(days=1), '%Y-%m-%d'),
        }





class report_project(models.AbstractModel):
    _name = 'report.deltatech_project.report_project'
    _inherit = 'report.abstract_report.project'
    _template = 'deltatech_project.report_project'

class report_project_do_today(models.AbstractModel):
    _name = 'report.deltatech_project.report_project_do_today'
    _inherit = 'report.abstract_report.project'
    _template = 'deltatech_project.report_project_do_today'

    
class report_project_do_tomorrow(models.AbstractModel):
    _name = 'report.deltatech_project.report_project_do_tomorrow'
    _inherit = 'report.abstract_report.project'
    _template = 'deltatech_project.report_project_do_tomorrow'

    
class report_project_do_on_date(models.AbstractModel):
    _name = 'report.deltatech_project.report_project_do_on_date'
    _inherit = 'report.abstract_report.project'
    _template = 'deltatech_project.report_project_do_on_date'
