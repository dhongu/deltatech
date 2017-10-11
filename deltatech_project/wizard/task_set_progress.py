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



class project_task_set_progress(models.TransientModel):
    _name = 'project.task.set.progress'
    _description = "Project Task Set Progress"
 

    project_progress = fields.Float(string='Progress for all task'  ) 



    @api.model
    def default_get(self, fields):
        defaults = super(project_task_set_progress, self).default_get(fields)
        task_ids = self.env.context.get('active_ids', False)
        
        tasks = self.env['project.task'].browse(task_ids)
        if not tasks:
            raise Warning(_('Select a task') )

        project_progress = 0
        for task in tasks:
            project_progress += task.project_progress
        

        defaults['project_progress'] = project_progress
        return defaults



    @api.multi
    def do_set_project_progress(self):

        task_ids = self.env.context.get('active_ids', False)
        
        tasks = self.env['project.task'].browse(task_ids)
        
        #actualizare procent 
        if self.project_progress and tasks:
            tasks.write({'project_progress':self.project_progress/len(tasks)})    
            
        action = self.env.ref('project.action_view_task').read()[0]  
        action['domain'] = "[('id','in', ["+','.join(map(str,tasks.ids))+"])]"
        return action

            
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

