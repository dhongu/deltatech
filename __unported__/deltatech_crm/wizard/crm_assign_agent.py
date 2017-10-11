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



class crm_assign_agent(models.TransientModel):
    _name = 'crm.assign.agent'
    _description = "CRM Assign agent"
    
    user_id =  fields.Many2one('res.users', string='Salesperson')

    @api.multi
    def do_assign(self):
        active_ids = self.env.context.get('active_ids', False)
        
        domain=[('type', '=', 'lead'),('user_id','=', False),('id','in', active_ids )] 
        
        leads = self.env['crm.lead'].search(domain)
        if leads:
            leads.write({'user_id':self.user_id.id})
        
        return True
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
