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



 
from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp

import urlparse


# pentru a preveni utilizarea unui template in care nu a fost inlocuit __URL__
class mail_compose_message(models.TransientModel):
    _inherit = 'mail.compose.message'

    @api.multi
    def send_mail(self):
        if self.body.find("__URL__") > 0:
                raise Warning( _("The content of the text contain '__URL__' "))

        res = super(mail_compose_message,self).send_mail()
        return res





class crm_new_survey(models.TransientModel):
    _name = 'crm.new.survey'
    _inherit = 'mail.compose.message'
    _description = "CRM New Survey Result"
    
    survey_id = fields.Many2one('survey.survey', string='Survey', required=True)
    partner_id = fields.Many2one('res.partner',   string='Partner', required=True)
    
    partner_ids = fields.Many2many('res.partner', 'crm_new_survey_res_partner_rel',
            'wizard_id', 'partner_id', string='Existing contacts')
    
    
    lead_id = fields.Many2one('crm.lead',   string='Lead')
    #by_mail = fields.Boolean('Send Email')
    #template_id = fields.Many2one('email.template', string='Template')

    @api.model
    def default_get(self, fields):      
        defaults = super(crm_new_survey, self).default_get(fields)
          
        active_id = self.env.context.get('active_id', False)
        lead = self.env['crm.lead'].browse(active_id) 
        defaults['lead_id'] = lead.id
        defaults['partner_id'] = lead.partner_id.id 
        if lead.partner_id:
            defaults['partner_ids'] = [(6,False, [lead.partner_id.id ])]
 
        defaults['mail_notify_noemail'] =  False
        defaults['mail_post_autofollow'] = False
              
        if lead.stage_id.survey_id:
            defaults['survey_id'] = lead.stage_id.survey_id.id
        else:
            if lead.categ_ids:
                defaults['survey_id'] = lead.categ_ids[0].survey_id.id
        return defaults

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            self.partner_ids |= self.partner_id

    @api.multi
    def make_survey(self):
        
        domain = [('lead_id','=',self.lead_id.id),
                  ('partner_id','=',self.partner_id.id),
                  ('survey_id','=',self.survey_id.id)
                  ]
        survey_result = self.env['survey.user_input'].search(domain)
        
        if not survey_result:
            value = {'lead_id':self.lead_id.id,'partner_id':self.partner_id.id,'survey_id':self.survey_id.id}
            survey_result = self.env['survey.user_input'].create(value)
        
        return survey_result
    
    @api.multi
    def do_new_survey(self):
        self.ensure_one()
        survey_result = self.make_survey()
        # {'type': 'ir.actions.act_window_close'}
        # si de aici se va deschide pagina pt introducerea de rezultate .....
        action = {
                    "type": "ir.actions.act_url",
                    "url": self.survey_id.public_url+'/'+survey_result.token,
                    "target": "self",
                }
        return action
                #http://dorin-ubuntu14:8069/survey/start/sondaj-1-3/223e2aca-e40f-4a5e-aac4-a92b3ab74001
        
    @api.multi
    def send_mail(self):
        if self.body.find("__URL__") < 0:
                raise Warning( _("The content of the text don't contain '__URL__'. \
                    __URL__ is automaticaly converted into the special url of the survey."))
                
        survey_result = self.make_survey()
        #set url
        url = self.survey_id.public_url

        url = urlparse.urlparse(url).path[1:]  # dirty hack to avoid incorrect urls

        url = url + '/' +survey_result.token

         
        self.body =  self.body.replace("__URL__", url)
        res = super(crm_new_survey,self).send_mail()
        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
