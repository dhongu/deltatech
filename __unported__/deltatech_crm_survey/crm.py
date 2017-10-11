# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
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



from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp


class crm_case_stage(models.Model):
    _inherit = "crm.case.stage"  
    survey_id = fields.Many2one('survey.survey', string='Survey')



class crm_case_categ(models.Model):
    _inherit = "crm.case.categ"  
    survey_id = fields.Many2one('survey.survey', string='Survey')
    

class crm_lead(models.Model):
    _inherit = "crm.lead"
    
    survey_results = fields.One2many('survey.user_input', 'lead_id', string="Survey Results")


    @api.multi
    def make_survey(self):
        self.ensure_one()
        
        template_id = self.stage_id.template_id.id
    
        # o fi mai bine daca modelul  este survey.survey?
        ctx.update({
            'default_model': 'crm.lead',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
         
        action = {
             'domain': False,
             'context': ctx,
             'view_type': 'form',
             'view_mode': 'form',
             'res_model': 'crm.new.survey',
              'target' : "new",
             'view_id': False,
             'type': 'ir.actions.act_window',
             'name' : _('New Survey Record'),
             'res_id': False
         }
        
        return   action





    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
