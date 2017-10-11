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
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp
from odoo.api import Environment
import threading


class service_plan_rescheduling(models.TransientModel):
    _name = 'service.plan.rescheduling'
    _description = "Service Plan Rescheduling"
    
    
    
    def do_rescheduling(self, cr, uid, ids, context=None):
        threaded_rescheduling = threading.Thread(target=self._background_rescheduling, args=(cr, uid, ids, context))
        threaded_rescheduling.start()        
        return {'type': 'ir.actions.act_window_close'}



    def _background_rescheduling(self, cr, uid, ids, context=None):
        """
        @param self: The object pointer.
        @param cr: A database cursor
        @param uid: ID of the user currently logged in
        @param ids: List of IDs selected
        @param context: A standard dictionary
        """
        with Environment.manage():
            new_cr = self.pool.cursor()
            self._calc_rescheduling(new_cr, uid, ids, context)
            new_cr.commit()
            new_cr.close()
            
        return {}        
           
    @api.multi
    def _calc_rescheduling(self):
         
        plans = self.env['service.plan'].search([('state','=','active')])
        plans.rescheduling()    
         
        message = _('Rescheduling executed in background was terminated')
        self.env.user.post_notification(title=_('Rescheduling'),message=message)           

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:    