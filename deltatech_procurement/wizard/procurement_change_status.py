# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2015 Deltatech All Rights Reserved
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


class procurement_change_status(models.TransientModel):
    _name = 'procurement.order.change.status'
    _description = 'Compute all schedulers'
    
    flag_cancel_no_check =  fields.Boolean(string="Cancel procurement without check")
    flag_cancel =  fields.Boolean(string="Cancel procurement")
    flag_run =  fields.Boolean(string="Run procurement")
    flag_check =  fields.Boolean(string="Check procurement")

    @api.multi
    def change_status(self):
        active_ids = self.env.context.get('active_ids', False)
        procurement_ids = self.env['procurement.order'].browse(active_ids)
        if self.flag_cancel:
            procurement_ids.cancel()
        if self.flag_check:
            procurement_ids.check()
        if self.flag_run:
            procurement_ids.run()
        if self.flag_cancel_no_check:
            for procurement in procurement_ids:
                moves_ok = True
                for move in procurement.move_ids:
                    if move.state not in ["draft", "cancel", "done", "assigned"]:
                        moves_ok = False
                if moves_ok:
                    for move in procurement.move_ids:
                        if move.state in ["draft", "assigned"]:
                            move.action_cancel()
                    procurement_ids.write( {'state': 'cancel'} )
            
        return {'type': 'ir.actions.act_window_close'}
        
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:






# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
