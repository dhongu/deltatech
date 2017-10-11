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
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta



class project_print_report_date(models.TransientModel):
    _name = 'project.print.report.date'
    _description = "Project Print Report Date"
 

    for_date = fields.Date(string="For Date",default=lambda * a:fields.Date.today())

    @api.multi
    def do_print(self):  
        data = {}
        data['for_date'] = self.for_date
        project_id = self.env.context.get('active_id', False)
        
        project = self.env['project.project'].browse(project_id)
        return self.env['report'].get_action( records = project, report_name='deltatech_project.report_project_do_on_date', data=data )
         

            
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

