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



from odoo import http
from odoo.http import request


class website_dasboard(http.Controller):
    @http.route(['/dashboard'], type='http', auth="user", website=True)
    def dashboard(self, start='', end='', **post):
        cr, uid, context = request.cr, request.uid, request.context

        domain = []
        if start and end:
            date_range = {'start': start, 'end': end}
        else:
            date_range = False

        tiles_obj = request.env['dashboard.tile']
        tiles = tiles_obj.with_context(date_range=date_range).search(domain)

        table_obj = request.env['dashboard.table']
        domain = []
        tables = table_obj.with_context(date_range=date_range).search(domain)

        graph_obj = request.env['dashboard.graph']
        domain = []
        graphs = graph_obj.with_context(date_range=date_range).search(domain)

        values = {
            'tiles': tiles,
            'tables': tables,
            'graphs': graphs
        }

        return request.render("website_dashboard.dashboard", values)
