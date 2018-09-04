# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2018 Deltatech All Rights Reserved
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
from openerp.http import Response
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug

from openerp import SUPERUSER_ID


class website_dasboard(http.Controller):
    @http.route(['/dashboard'], type='http', auth="user", website=True)
    def dashboard(self, start='', end='', **post):
        cr, uid, context = request.cr, request.uid, request.context
        tiles_obj = request.registry['dashboard.tile']
        domain = []
        if start and end:
            context['date_range'] = {'start': start, 'end': end}

        tile_ids = tiles_obj.search(cr, uid, domain, order='sequence', context=context)
        tiles = tiles_obj.browse(cr, uid, tile_ids, context=context)

        table_obj = request.registry['dashboard.table']
        domain = []
        table_ids = table_obj.search(cr, uid, domain, order='sequence', context=context)
        tables = table_obj.browse(cr, uid, table_ids, context=context)

        graph_obj = request.registry['dashboard.graph']
        domain = []
        graph_ids = graph_obj.search(cr, uid, domain, order='sequence', context=context)
        graphs = graph_obj.browse(cr, uid, graph_ids, context=context)

        values = {
            'tiles': tiles,
            'tables': tables,
            'graphs': graphs
        }

        return request.website.render("website_dashboard.dashboard", values)

