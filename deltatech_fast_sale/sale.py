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


class sale_order(models.Model):
    _inherit = 'sale.order' 
    

    @api.multi
    def action_button_confirm_to_invoice(self): 
        if self.state == 'draft':     
            self.action_button_confirm()  # confirma comanda
        for picking in self.picking_ids:
            picking.action_assign()   # verifica disponibilitate
            if not all(move.state == 'assigned' for move in picking.move_lines):
                raise Warning(_('Not all products are available.')   )
            picking.do_transfer()
  
        action_obj = self.env.ref('stock_account.action_stock_invoice_onshipping')
        action = action_obj.read()[0]

        if picking_ids:
            action['context'] =  {'active_ids': self.picking_ids.ids, 
                                  'active_id': self.picking_ids[0].id  } 
        return   action

    


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
