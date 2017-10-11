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



class project_task_recurrence(models.TransientModel):
    _name = 'project.task.recurrence'
    _description = "Project Task Recurrence"
 
 
    task_id = fields.Many2one('project.task',string='Base Task', readonly=True )
    first_date = fields.Datetime(string='First Recurrence Date', required=True ,)
    last_date  = fields.Datetime(string='Last Recurrenc Date', required=True ,)
    
    day_start = fields.Integer('Start day of month')
    day_end   = fields.Integer('End day of month')
    
    interval =  fields.Integer('Repeat Every', help="Repeat every (Days/Week/Month)")
    cycle  = fields.Selection([('day','Day'), ('week','Week'), ('month','Month') ],  string= 'Cycle', default='month' )
    project_progress = fields.Float(string='Progress for all task'  ) 



    @api.model
    def default_get(self, fields):
        defaults = super(project_task_recurrence, self).default_get(fields)
        task_id = self.env.context.get('active_id', False)
        task = self.env['project.task'].browse(task_id)
        if not task:
            raise Warning(_('Select a task') )
        if task.recurrence:
            raise Warning(_('The task is already recurrence') )
        
        defaults['task_id'] = task.id
        defaults['first_date'] = task.date_deadline
        defaults['last_date'] = task.project_id.date
        defaults['project_progress'] = task.project_progress
        return defaults

    @api.model
    def get_cyle(self):
        self.ensure_one()
        if self.cycle == 'day':
            return  timedelta(days=self.interval)
        if self.cycle == 'week':
            return  timedelta(weeks=self.interval)             
        if self.cycle == 'month':
            return  relativedelta(months=+self.interval) #monthdelta(self.value)  
        if self.cycle == 'year':
            return  relativedelta(years=+self.interval)

    @api.multi
    def do_recurrence(self):
        self.ensure_one()
        recurrence_tasks=[]
        first_date = fields.Date.from_string(self.first_date) 
        last_date = fields.Date.from_string(self.last_date)

        next_date = first_date 
        next_start_date = first_date  
 
        while next_date < last_date :  
            if self.cycle=='month':
                if self.day_end < 0:
                    next_date += relativedelta(day=1,months=1) #Getting 1st of next month
                    next_date += relativedelta(days=self.day_end )
                if self.day_end > 0:
                    next_date += relativedelta(day=self.day_end , months=0)            
            
                if self.day_start < 0:
                    next_start_date += relativedelta(day=1,months=1) #Getting 1st of next month
                    next_start_date += relativedelta(days=self.day_start )
                if self.day_start > 0:
                    next_start_date += relativedelta(day=self.day_start , months=0)               
            
            recurrence_tasks += [{'name':self.task_id.name,
                                  'date_start':fields.Date.to_string(next_start_date),
                                 'date_end':fields.Date.to_string(next_date),
                                 'date_deadline':fields.Date.to_string(next_date),
                                 'current': False,
                                 'kanban_state' :'blocked',
                                 'recurrence':True}]
            
            next_date +=  self.get_cyle()
            next_start_date +=  self.get_cyle()
        # end while
        
        if recurrence_tasks:
            firs_task_value = recurrence_tasks.pop(0)
            self.task_id.write({'date_start':firs_task_value['date_start'],
                                'date_end':firs_task_value['date_end'],
                                'date_deadline':firs_task_value['date_deadline'], })
        prev_task = self.task_id
        tasks = self.env['project.task']
        tasks |= self.task_id
        for recurrence_task in recurrence_tasks: 
            new_task = self.task_id.copy(recurrence_task)
            tasks |= new_task
            prev_task.write({'recurrence':True,
                             'next_recurrent_task':new_task.id})
            prev_task = new_task
        
        #actualizare procent 
        if self.project_progress and tasks:
            tasks.write({'project_progress':self.project_progress/len(tasks)})
            
            
        action = self.env.ref('project.action_view_task').read()[0]  
        action['domain'] = "[('id','in', ["+','.join(map(str,tasks.ids))+"])]"
        return action

            
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

