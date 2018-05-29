# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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

 


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, ValidationError, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
 
import time
from datetime import datetime, timedelta, date

class hr_attendance(models.Model):
    _inherit = "hr.attendance"
    for_date = fields.Datetime(string='For Date', compute="_compute_for_date", store=True)
    
    
    @api.multi
    @api.depends('name') 
    def _compute_for_date(self):
        for attendance in self:
            for_date = fields.Datetime.from_string(attendance.name) - timedelta(hours=7)
            attendance.for_date = fields.Datetime.to_string(for_date)
             
            
         
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: