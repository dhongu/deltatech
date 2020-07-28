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



    
class crm_lead(models.Model):
    _inherit = "crm.lead"
    
    doc_count = fields.Integer(string="Number of documents attached", compute = "_compute_doc_count")


    @api.one
    def _compute_doc_count(self):
        
        leads_docs = self.env['ir.attachment'].search([('res_model', '=', 'crm.lead'), ('res_id', '=', self.id)], count=True)
        if self.ref and self.ref._name=='sale.order':
            sale_orders = self.env['ir.attachment'].search([('res_model', '=', 'sale.order'), ('res_id', '=',  self.ref.id)], count=True)
        else:
            sale_orders = 0
        
        self.doc_count = leads_docs + sale_orders


    @api.multi
    def attachment_tree_view(self):

        if self.ref and self.ref._name == 'sale.order':
            sale_order_ids = self.ref.ids
        else:
            sale_order_ids = []
            
        domain = [
             '|',
             '&', ('res_model', '=', 'crm.lead'), ('res_id', 'in', self.ids),
             '&', ('res_model', '=', 'sale.order'), ('res_id', 'in', sale_order_ids)]
        
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







# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
