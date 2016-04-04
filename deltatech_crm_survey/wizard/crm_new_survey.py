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
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp

class crm_new_survey(models.TransientModel):
    _name = 'crm.new.survey'
    _description = "CRM New Survey Result"
    
    survey_id = fields.Many2one('survey.survey', string='Survey', required=True)
    partner_id = fields.Many2one('res.partner',   string='Partner', required=True)
    lead_id = fields.Many2one('res.partner',   string='Partner')
    

    @api.model
    def default_get(self, fields):      
        defaults = super(crm_new_survey, self).default_get(fields)
          
        active_id = self.env.context.get('active_id', False)
        lead = self.env['crm.lead'].browse(active_id) 
        defaults['lead_id'] = lead.id
        defaults['partner_id'] = lead.partner_id.id 
        if lead.stage_id.survey_id:
            defaults['survey_id'] = lead.stage_id.survey_id.id
        else:
            if lead.categ_ids:
                defaults['survey_id'] = lead.categ_ids[0].survey_id.id
        return defaults
    
    @api.multi
    def do_new_survey(self):
        self.ensure_one()
        domain = [('lead_id','=',self.lead_id.id),
                  ('partner_id','=',self.partner_id.id),
                  ('survey_id','=',self.survey_id.id)
                  ]
        survey_result = self.env['survey.user_input'].search(domain)
        
        if not survey_result:
            value = {'lead_id':self.lead_id.id,'partner_id':self.partner_id.id,'survey_id':self.survey_id.id}
            survey_result = self.env['survey.user_input'].create(value)
        
        # si de aici se va deschide pagina pt introducerea de rezultate .....
        action = {
                    "type": "ir.actions.act_url",
                    "url": self.survey_id.public_url+'/'+survey_result.token,
                    "target": "new",
                }
        return action
                #http://dorin-ubuntu14:8069/survey/start/sondaj-1-3/223e2aca-e40f-4a5e-aac4-a92b3ab74001
        



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
