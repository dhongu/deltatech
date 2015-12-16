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

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
from openerp.tools import float_is_zero
 
 
 
class project_task_type(models.Model):
    _inherit = 'project.task.type'

    use_progress = fields.Boolean()
    progress = fields.Float(string='Progress')


class project_project(models.Model):
    _inherit = "project.project"


    categ_id = fields.Many2one('project.category', string='Category')
    project_parent_id = fields.Many2one('project.project',  string='Parent Project') #compute='_get_project_parent_id', inverse="_set_project_parent_id", store=True,
    project_child_ids = fields.One2many('project.project', 'project_parent_id', string='Child Projects')
    parent_id = fields.Many2one('account.analytic.account')

    child_count = fields.Integer(compute='_get_project_child_count',  string="Child Projects Count")
    progress_rate = fields.Float(string='Progress', compute='_compute_progress_rate', store=False,   digits=(16,2) ) #,

    task_count = fields.Integer( compute='_task_count',  string="Tasks")

    @api.multi
    @api.depends('task_ids')
    def _task_count(self):
        for project in self:
            project.task_count = 0
            for task in project.task_ids:
                if task.current:
                    project.task_count += 1
    
    @api.multi
    @api.onchange('parent_id')
    def onchange_parent_id(self): 
        for project in self:
            if project.parent_id:
                project.project_parent_id = self.search([('analytic_account_id','=',project.parent_id.id)])

    @api.multi
    @api.onchange('project_parent_id')
    def onchange_project_parent_id(self): 
        for project in self:
            project.parent_id = self.project_parent_id.analytic_account_id

 
                
    @api.multi
    @api.depends('project_child_ids')
    def _get_project_child_count(self):
        for project in self:
             project.child_count = len(project.project_child_ids)
 
    @api.multi
    def name_get(self):
        res = []
        for project_item in self:
            data = [] 
            if project_item.code:
                data = '['+ project_item.code +']'+project_item.name
            else:
                data = project_item.name        
            res.append((project_item.id, data))
        return res

    
    @api.model
    def get_tasks_progress(self):
        progress = []
        for task in self.tasks:
            if task.current:
                progress += [task.progress]
        if self.project_child_ids:
            for child in self.project_child_ids:
               progress += child.get_tasks_progress()
        
        return progress

    #         
    @api.multi
    @api.depends('task_ids.progress')  
    def _compute_progress_rate(self):
        for project in self:
            progress = project.get_tasks_progress()
            if progress:
                project.progress_rate = sum(progress) / len(progress)
            else:
                project.progress_rate = 0.0           
 
    @api.multi
    def update_progress(self):
        for project in self:
            progress = project.get_tasks_progress()
            if progress:
                progress_rate =  round(sum(progress) / len(progress), 2)
            else:
                progress_rate = 0.0
            project.write({'progress_rate':progress_rate})
            print project.name, progress_rate
            if  project.project_parent_id:
                project.project_parent_id.update_progress()         
                
    @api.model
    def default_get(self, fields):
        defaults = super(project_project, self).default_get(fields)
        project_parent_id = self.env.context.get('active_id', False) 
        project_parent = self.browse(project_parent_id) 
        if project_parent_id:
            defaults['project_parent_id'] = project_parent.id
            defaults['date_start'] = project_parent.date_start
            defaults['date'] = project_parent.date
            defaults['color'] = project_parent.color
        return defaults
                
class project_task(models.Model):
    _inherit = "project.task"
    
    progress = fields.Float(string='Progress', compute='_get_progress',store=True)
    recurrence = fields.Boolean(string="Recurrence")
    current = fields.Boolean(string='Current Task', default=True, copy=False, compute='_get_current', store=True)  # se va actualiza cu CRON
    #recurrent_ids = fields.Many2many('project.task', relation='project_task_to_task_recurrence', column1='main_task_id', column2='task_id')
    next_recurrent_task = fields.Many2one('project.task',string='Next Task', copy=False)
     
    doc_count = fields.Integer(string="Number of documents attached", compute='_get_attached_docs')



    @api.multi
    def _get_attached_docs(self):
        for task in self:
            task.doc_count =  self.env['ir.attachment'].search_count([('res_model', '=', 'project.task'), ('res_id', '=', task.id)])
            

    @api.multi
    @api.depends('date_start','date_end')
    def _get_current(self):
        for task in self:
            if task.recurrence:           
                if task.progress < 100:
                    task.current = True
                else:
                    if task.date_start < fields.Datetime.now() < task.date_end: 
                        task.current = True
                    else:
                        task.current = False
            else:
                task.current = True

    
                    

    @api.multi
    @api.depends('work_ids', 'remaining_hours', 'planned_hours',  'stage_id')
    def _get_progress(self):
        if self.ids:
            self.env.cr.execute("SELECT task_id, COALESCE(SUM(hours),0) FROM project_task_work WHERE task_id IN %s GROUP BY task_id",(tuple(self.ids),))
            hours = dict(self.env.cr.fetchall())
            for task in self:   
                task.effective_hours =  hours.get(task.id, 0.0)
                task.total_hours =  (task.remaining_hours or 0.0) + hours.get(task.id, 0.0)    
                task.delay_hours = task.total_hours - task.planned_hours
                task.progress = 0.0
                          
                if not float_is_zero(task.total_hours, precision_digits=2):
                    task.progress = round(min(100.0 * hours.get(task.id, 0.0) / task.total_hours, 99.99),2)
                if task.stage_id and  task.stage_id.use_progress:
                    task.progress = task.stage_id.progress


            
            

    @api.onchange('date_deadline')
    def on_change_date_deadline(self):
        if self.date_deadline:
            if not self.date_end or self.date_end < self.date_deadline:
                self.date_end = self.date_deadline + fields.Datetime.now()[-9:]
                if self.date_start > self.date_end:
                    self.date_start = self.date_end


    @api.multi
    def write(self, vals):
        res = super(project_task,self).write(vals)
        
        common_fields = ['name','project_id','description']
        recurrence_values = {}
        for field in common_fields:
            if vals.get(field,False):
                recurrence_values[field] = vals[field]
                
        if vals.get('kanban_state',False):
            for task in self:
                if task.recurrence:
                    if task.next_recurrent_task:
                        if vals['kanban_state'] == 'done':
                            task.next_recurrent_task.write({'kanban_state':'normal'}) 
                        else:
                            if  task.next_recurrent_task.kanban_state == 'normal':
                                task.next_recurrent_task.write({'kanban_state':'blocked'})            
        
        if recurrence_values:
            for task in self:
                if task.recurrence:
                    if task.next_recurrent_task:
                        task.next_recurrent_task.write(recurrence_values)
        """
        if vals.get('progress',False):
            for task in self:
                if task.project_id:
                    task.project_id.update_progress()
        """            
        return res

    @api.multi
    def unlink(self):
        for task in self:
            if task.next_recurrent_task:
                task.next_recurrent_task.unlink()
        return  super(project_task,self).unlink()


    def attachment_tree_view(self, cr, uid, ids, context):
        
        domain = [ '&', ('res_model', '=', 'project.task'), ('res_id', 'in', ids)]
        res_id = ids and ids[0] or False
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, res_id)
        }

    @api.model
    def default_get(self, fields):
        defaults = super(project_task, self).default_get(fields)
        if not defaults.get('project_id', False): 
            project_id = self.env.context.get('active_id', False) 
        else:
            project_id = defaults['project_id']
        project= self.env['project.project'].browse(project_id) 
        if project:
            defaults['project_id'] = project.id
            defaults['date_start'] = project.date_start
            defaults['date_end'] = project.date
            defaults['date_deadline'] = project.date
            defaults['color'] = project.color
        return defaults

    @api.model
    def  cron_update(self):
        tasks = self.search([('recurrence','=',True)])
        tasks._get_current()
            

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

