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

 
import time
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import werkzeug.urls
from werkzeug.exceptions import NotFound

from openerp import http
from openerp import tools
from openerp.http import request
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug

from openerp import SUPERUSER_ID


class website_service(http.Controller):

    @http.route(['/service/equipment/update_status/<ean_code>'], type='json', auth="public", website=True)
    def update_status(self,  ean_code=None, **post):
        ret = []
        equipment_obj = request.registry['service.equipment']
        
        equipment_id = equipment_obj.search(request.cr, request.uid, [('ean_code','=',ean_code)], context=request.context)
        
        if not equipment_id:
            return False
        
        equipment = equipment_obj.browse(request.cr, SUPERUSER_ID, equipment_id)

        

        return ret     
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
