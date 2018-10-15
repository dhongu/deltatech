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

import base64


class sale_rfq(models.Model):
    _name = "sale.rfq"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = "Sale Request For Quotation"
    _order = "request_date desc"

    name = fields.Char(string='Name', index=True, default="/", copy=False )
    
    order_id = fields.Many2one('sale.order', string="Quotation", readonly=True, states={'draft': [('readonly', False)], 'in_progress': [('readonly', False)]},)
    lead_id = fields.Many2one('crm.lead', string='Opportunity',required=True, readonly=True, states={'draft': [('readonly', False)]},)
    partner_id = fields.Many2one('res.partner', string='Customer', related="lead_id.partner_id",  readonly=True, states={'draft': [('readonly', False)]} ,store=True )    # Clientul
    
    team_leader_id = fields.Many2one('res.users', #related="lead_id.section_id.user_id", 
                                     string='Team Leader',track_visibility='always', readonly=True, states={'draft': [('readonly', False)]})
    
    salesperson_id = fields.Many2one('res.users', string='Salesperson',  related="lead_id.user_id" ) 
    
    requester_id = fields.Many2one('res.users', string='Requester',
                                   required=True, default=lambda self: self.env.user.id,
                                   readonly=True, 
                                   states={'draft': [('readonly', False)]},
                                   track_visibility='always')  # Solicitant
    
    request_date = fields.Date('Request Date', default=lambda * a:fields.Date.today(), readonly=True, states={'draft': [('readonly', False)]})
    designer_id = fields.Many2one('res.users', string='Designer', 
                                  states={'draft': [('readonly', False)]},
                                  track_visibility='always')    # Devizier
    
    date_deadline = fields.Date(string='Deadline', readonly=True, states={'draft': [('readonly', False)]})
    
    report_id = fields.Many2one('ir.actions.report.xml', string='Report', domain=[('model','=','sale.order')] )
    
    doc_count = fields.Integer(string="Number of documents attached", compute = "_compute_doc_count")
 
    state = fields.Selection([('draft','Draft'),          # starea initiala generata de requester
                              ('adjusting','Adjusting'),  # se va seta daca devizul trebuie refacut
                              ('in_progress','In Progress'),
                              
                              ('prepared','Prepared'),    # se va seta dupa ce se va intocmi primul deviz
                              ('sent', 'Quotation Sent'), # se va seta dupa ce devizul va fi trmis  
                              
                              ('canceled','Canceled'),
                              ('done','Done')],
                             string='Status', index=True, readonly=True, default='draft',
                             track_visibility='onchange', copy=False,)
    note = fields.Text(string="Note")

    @api.onchange('lead_id')
    def onchange_lead_id(self):
        self.team_leader_id = self.lead_id.section_id.user_id

    @api.model
    def create(self,   vals ):  
        if ('name' not in vals) or (vals.get('name') in ('/', False)):
            sequence = self.env.ref('deltatech_sale_rfq.sequence_sale_rfq')
            if sequence:
                vals['name'] = self.env['ir.sequence'].next_by_id(sequence.id)    
        return super(sale_rfq, self).create( vals )


    @api.multi
    def unlink(self):
        for rfq in self:
            if rfq.state not in ('draft'):
                raise Warning(_('You cannot delete a RFQ which is not draft.'))
        return super(sale_rfq, self).unlink() 

    @api.model
    def get_link(self, model ):
        for model_id, model_name in model.name_get():
            link = "<a href='#id=%s&model=%s'>%s</a>" % (str(model_id), model._name, model_name )
        return link

    @api.one
    def _compute_doc_count(self): 
        sale_rfq_docs = self.env['ir.attachment'].search([('res_model', '=', 'sale.rfq'), ('res_id', '=', self.id)], count=True)   
        leads_docs = self.env['ir.attachment'].search([('res_model', '=', 'crm.lead'), ('res_id', '=', self.lead_id.id)], count=True)
        #sale_orders = self.env['ir.attachment'].search([('res_model', '=', 'sale.order'), ('res_id', '=', self.order_id.id)], count=True)        
        self.doc_count = sale_rfq_docs + leads_docs # + sale_orders 

    @api.multi
    def attachment_tree_view(self): 
        domain = [
             '|', 
             '&', ('res_model', '=', 'sale.rfq'), ('res_id', '=', self.id),
             '&', ('res_model', '=', 'crm.lead'), ('res_id', '=', self.lead_id.id) ]
        
        context = {
                   'default_res_model': self._name, 
                   'default_res_id':self.id,
                   'default_partner_id':self.partner_id.id
                   }
        
        return {
            'name': _('Attachments'),
            'domain': domain,
            'res_model': 'ir.attachment',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'kanban,tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': context,
            #'context': "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        }


    def _message_get_auto_subscribe_fields(self, cr, uid, updated_fields, auto_follow_fields=None, context=None):
        auto_follow_fields = ['requester_id', 'designer_id','team_leader_id']
        return super(sale_rfq, self)._message_get_auto_subscribe_fields(cr, uid, updated_fields, auto_follow_fields, context=context)

    
    @api.multi
    def new_quotation(self):
        self.ensure_one()
        
        
        partner = self.partner_id
        partner_addr = partner.address_get(['default', 'invoice', 'delivery', 'contact'])
        pricelist = partner.property_product_pricelist.id
        fpos = partner.property_account_position and partner.property_account_position.id or False
        payment_term = partner.property_payment_term and partner.property_payment_term.id or False
        if False in partner_addr.values():
            raise Warning(_('Insufficient Data!'), _('No address(es) defined for this customer.'))
        
        vals = {
                    'origin': _('Opportunity: %s') % self.lead_id.name,
                    'section_id': self.lead_id.section_id and self.lead_id.section_id.id or False,
                    'user_id': self.salesperson_id.id,
                    'partner_id': partner.id,
                    'pricelist_id': pricelist,
                    'partner_invoice_id': partner_addr['invoice'],
                    'partner_shipping_id': partner_addr['delivery'],
                    'date_order': fields.Datetime.now(),
                    'fiscal_position': fpos,
                    'payment_term':payment_term,
                    
                }
        order_id = self.env['sale.order'].create(vals)
        self.write({'order_id':order_id.id})
        
        message = _("Opportunity %s has been <b>converted</b> to the quotation <em>%s</em>.") % (self.get_link(self.lead_id), self.get_link(order_id) )
        self.lead_id.message_post(body=message)
        self.message_post(body=message)
        


    @api.multi
    def quotation_ready(self):
        for rfq in self:
            rfq.write({'state':'prepared'})
            if rfq.report_id:
                report_service = rfq.report_id.report_name
                result = self.env['report'].get_pdf(rfq.order_id,report_service)
                report_name = rfq.order_id.name + '.pdf'
                #print result
                attachments = []
                #result = base64.b64encode(result)
                attachments.append((report_name, result))
                
                message = _("Quotation %s is ready") % ( self.get_link(rfq.order_id) )
                rfq.message_post(body=message,attachments=attachments) 
                rfq.lead_id.message_post(body=message,attachments=attachments) 
                
                message = _("RFQ %s is ready") % ( self.get_link(rfq) )
                rfq.order_id.message_post(body=message) 
                
                            
            else:
                 Warning(_('Please enter report template'))

    @api.multi
    def quotation_start(self):
        self.write({'state':'in_progress'})        


    @api.multi
    def quotation_send(self):
        self.write({'state':'sent'})


    @api.multi
    def quotation_adjust(self):
        self.write({'state':'adjusting'})
 
 
    @api.multi
    def quotation_done(self):
        self.write({'state':'done'})        

    @api.multi
    def quotation_cancel(self):
        self.write({'state':'canceled'})

 
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
