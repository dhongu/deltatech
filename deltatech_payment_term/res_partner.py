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

 
 


class res_partner(models.Model):
    _inherit = "res.partner"
    
 
    @api.multi
    def view_rate(self):
        action = self.env.ref('deltatech_payment_term.action_account_moves_sale').read()[0]         
        action['domain'] = "[('partner_id','=',"+str(self.id)+" )]"        
        return action          
 
            

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
