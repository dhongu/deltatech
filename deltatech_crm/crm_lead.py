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

    


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
