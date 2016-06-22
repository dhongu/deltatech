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



from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp import models, fields, api, _, tools
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
import openerp.addons.decimal_precision as dp
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta



class crm_lead(models.Model):
    _inherit = "crm.lead"

    team_id = fields.Many2one('crm.case.section', string='Sales Team', related='section_id')

    # CRM Actions
    last_activity_id = fields.Many2one("crm.activity", string="Last Activity", select=True)
    next_activity_id = fields.Many2one("crm.activity", string="Next Activity", select=True)
    next_activity_1 = fields.Char(related="last_activity_id.activity_1_id.name",  string="Next Activity 1")
    next_activity_2 = fields.Char(related="last_activity_id.activity_2_id.name",  string="Next Activity 2")
    next_activity_3 = fields.Char(related="last_activity_id.activity_3_id.name",  string="Next Activity 3")
     


    @api.multi
    def action_send_email(self):
        '''
        This function opens a window to compose an email, with the template message loaded by default
        '''
        
        self.ensure_one()
        
        template_id = self.stage_id.template_id.id
        try:
            compose_form_id = self.env['ir.model.data'].get_object_reference( 'mail', 'email_compose_message_wizard_form')[1]
        except ValueError:
            compose_form_id = False 
        ctx = dict()
        ctx.update({
            'default_model': 'crm.lead',
            'default_res_id': self.id,
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_so_as_sent': True
        })
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }



    @api.model
    def message_new(self,  msg_dict, custom_values=None):
              
        res = super(crm_lead,self).message_new(  msg_dict, custom_values)
            
        if custom_values is None:
            custom_values = {} 
        
        print custom_values
        try:    
            xml_body = html.fromstring(msg_dict['body'])
        except Exception as e:
            print e
            return res
        
        try:  
            element = xml_body.xpath("//*[@itemprop='addressLocality']")
            if  element:
                custom_values['city'] =  element[0].text
        except Exception as e:
            print e
            pass
        
        try:  
            element = xml_body.xpath("//*[@itemprop='telephone']")
            if  element:
                custom_values['phone'] =  element[0].text
        except Exception as e:
            print e
            pass
        
        try:
            element = xml_body.xpath("//*[@itemprop='streetAddress']")
            if  element:
                custom_values['street'] =  element[0].text
        except Exception as e:
            print e
            pass
        
        try:            
            element = xml_body.xpath("//*[@itemprop='addressRegion']")
            if  element:
                region = self.env['res.country.state'].name_search(element[0].text)
                if region:
                    custom_values['state_id'] =  region.id
                    custom_values['country_id'] =  region.country_id.id
                else:
                    custom_values['street'] += element[0].text
        except Exception as e:
            print e
            pass
        
        try:    
            element = xml_body.xpath("//*[@itemprop='addressCountry']")
            if  element:
                country = self.env['res.country'].name_search(element[0].text)
                if country:
                    custom_values['country_id'] =  country.id
                else:
                    if not custom_values['country_id']:
                        custom_values['street'] += element[0].text
        except Exception as e:
            print e
            pass
        
        try:         
            element = xml_body.xpath("//address//*[@itemprop='name']")
            if  element:
                custom_values['contact_name'] =  element[0].text
        except Exception as e:
            print e
            pass
        
        try:         
            element = xml_body.xpath("//address//*[@itemprop='email']")
            if  element:
                custom_values['email_from'] =  element[0].text
        except Exception as e:
            print e
            pass
        
        try:         
            element = xml_body.xpath("//*[@itemprop='maildomain']")
            if  element:
                medium = self.env['crm.tracking.medium'].search([('name','like',element[0].text)])
                if medium:
                    custom_values['medium_id'] =  medium.id
        except Exception as e:
            print e
            pass
        
        print custom_values              
        return res

    @api.multi
    def show_quotation(self): 
        self.ensure_one()
        if not self.ref:
            return True
        
        if not self.ref._name=='sale.order':
            return True
  
        ##action_obj = self.env.ref('sale.action_orders')
        ##action = action_obj.read()[0]
 
        action = {
                 'domain': str([('id', 'in', self.ref.id)]),
                 'view_type': 'form',
                 'view_mode': 'form',
                 'res_model': 'sale.order',
                 'view_id': False,
                 'type': 'ir.actions.act_window',
                 'name' : _('Quotation'),
                 'res_id': self.ref.id
             }

        return   action

    @api.multi
    def log_next_activity_1(self):
        return self.set_next_activity( next_activity_name='activity_1_id')

    @api.multi
    def log_next_activity_2(self):
        return self.set_next_activity( next_activity_name='activity_2_id')

    @api.multi
    def log_next_activity_3(self):
        return self.set_next_activity( next_activity_name='activity_3_id')

    @api.multi
    def set_next_activity(self,  next_activity_name):
        for lead in self:
            if not lead.last_activity_id:
                continue
            next_activity = next_activity_name and getattr(lead.last_activity_id, next_activity_name, False) or False
            if next_activity:
                date_action = False
                if next_activity.days:
                    date_action = (datetime.now() + timedelta(days=next_activity.days)).strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT),
                lead.write({
                    'next_activity_id': next_activity.id,
                    'date_action': date_action,
                    'title_action': next_activity.description,
                })
        return True


    #todo: de utilizat un tamplate pentru email
    @api.multi
    def log_next_activity_done(self):
        to_clear_ids = self.env['crm.lead']
        for lead in self:
            
            if not lead.next_activity_id:
                continue
            body_html = """<div><b>${object.next_activity_id.name}</b></div>
%if object.title_action:
<div>${object.title_action}</div>
%endif"""
            body_html = self.env['email.template'].render_template(body_html, 'crm.lead', lead.id)
            msg_id = lead.message_post(body_html, subtype_id=lead.next_activity_id.subtype_id.id)
            msg = self.env['mail.message'].browse(msg_id)
            msg.write({'subtype_id':lead.next_activity_id.subtype_id.id})
            to_clear_ids |= lead
            lead.write({'last_activity_id': lead.next_activity_id.id})

        if to_clear_ids:
            to_clear_ids.cancel_next_activity()
        return True

    @api.multi
    def cancel_next_activity(self):
        return self.write( {
            'next_activity_id': False,
            'date_action': False,
            'title_action': False,
        })

    def onchange_next_activity_id(self, cr, uid, ids, next_activity_id, context=None):
        if not next_activity_id:
            return {'value': {
                'next_action1': False,
                'next_action2': False,
                'next_action3': False,
                'title_action': False,
                'date_action': False,
            }}
        activity = self.pool['crm.activity'].browse(cr, uid, next_activity_id, context=context)
        date_action = False
        if activity.days:
            date_action = (datetime.now() + timedelta(days=activity.days)).strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
        return {'value': {
            'next_activity_1': activity.activity_1_id and activity.activity_1_id.name or False,
            'next_activity_2': activity.activity_2_id and activity.activity_2_id.name or False,
            'next_activity_3': activity.activity_3_id and activity.activity_3_id.name or False,
            'title_action': activity.description,
            'date_action': date_action,
            'last_activity_id': False,
        }}    

    """
    "" nu este ok ca in context nu am active_id
    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        if view_type == 'form':
            active_id = self.env.context.get('active_id',False)
          
            if active_id:
                lead = self.env['crm.lead'].browse(active_id)
                if lead.type == 'opportunity':
                    view_id = self.env.ref('crm.crm_case_form_view_oppor').id
        
        res = super(crm_lead, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        return res
    """

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
