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

from odoo.report import report_sxw
from odoo.osv import osv



class report_project_wrapper(report_sxw.rml_parse):

    def __init__(self, cr, uid, name, context):
        super(report_project_wrapper, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'datetime': datetime,
            'today': time.strftime('%Y-%m-%d'),
            'tomorrow':datetime.datetime.strftime(datetime.date.today() + datetime.timedelta(days=1),'%Y-%m-%d'),
        })


class report_project(osv.AbstractModel):
    _name = 'report.deltatech_project.report_project'
    _inherit = 'report.abstract_report'
    _template = 'deltatech_project.report_project'
    _wrapped_report_class = report_project_wrapper


class report_project_do_today(osv.AbstractModel):
    _name = 'report.deltatech_project.report_project_do_today'
    _inherit = 'report.abstract_report'
    _template = 'deltatech_project.report_project_do_today'
    _wrapped_report_class = report_project_wrapper
    
    
class report_project_do_tomorrow(osv.AbstractModel):
    _name = 'report.deltatech_project.report_project_do_tomorrow'
    _inherit = 'report.abstract_report'
    _template = 'deltatech_project.report_project_do_tomorrow'
    _wrapped_report_class = report_project_wrapper
    
    
class report_project_do_on_date(osv.AbstractModel):
    _name = 'report.deltatech_project.report_project_do_on_date'
    _inherit = 'report.abstract_report'
    _template = 'deltatech_project.report_project_do_on_date'
    _wrapped_report_class = report_project_wrapper
 

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
