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
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp import SUPERUSER_ID, api
import openerp.addons.decimal_precision as dp


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

    def log_next_activity_1(self, cr, uid, ids, context=None):
        return self.set_next_activity(cr, uid, ids, next_activity_name='activity_1_id', context=context)

    def log_next_activity_2(self, cr, uid, ids, context=None):
        return self.set_next_activity(cr, uid, ids, next_activity_name='activity_2_id', context=context)

    def log_next_activity_3(self, cr, uid, ids, context=None):
        return self.set_next_activity(cr, uid, ids, next_activity_name='activity_3_id', context=context)

    def set_next_activity(self, cr, uid, ids, next_activity_name, context=None):
        for lead in self.browse(cr, uid, ids, context=context):
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

    def log_next_activity_done(self, cr, uid, ids, context=None, next_activity_name=False):
        to_clear_ids = []
        for lead in self.browse(cr, uid, ids, context=context):
            if not lead.next_activity_id:
                continue
            body_html = """<div><b>${object.next_activity_id.name}</b></div>
%if object.title_action:
<div>${object.title_action}</div>
%endif"""
            body_html = self.pool['mail.template'].render_template(cr, uid, body_html, 'crm.lead', lead.id, context=context)
            msg_id = lead.message_post(body_html, subtype_id=lead.next_activity_id.subtype_id.id)
            to_clear_ids.append(lead.id)
            self.write(cr, uid, [lead.id], {'last_activity_id': lead.next_activity_id.id}, context=context)

        if to_clear_ids:
            self.cancel_next_activity(cr, uid, to_clear_ids, context=context)
        return True

    def cancel_next_activity(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids,  {
            'next_activity_id': False,
            'date_action': False,
            'title_action': False,
        }, context=context)

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


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
