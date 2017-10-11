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

 

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT,DEFAULT_SERVER_TIME_FORMAT
 

 

class res_users_gamification_group(models.Model):
    _inherit =  'res.users' 

    def _serialised_goals_summary(self, cr, uid, user_id, excluded_categories=None, context=None):        
        if context is None:
            context = {}
            user = self.browse(cr, uid, uid, context=context)
            context['lang'] =  user.lang
        return super(res_users_gamification_group,self)._serialised_goals_summary(cr, uid, user_id, excluded_categories, context) 



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
