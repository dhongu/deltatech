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

from openerp import models, fields, api, _
from openerp import SUPERUSER_ID
from openerp.addons.web.http import request
from openerp.tools.translate import _
from sys import maxint


class website(models.Model):
    _inherit = 'website'

    @api.multi
    def sale_product_domain(self):
        domain = super(website, self).sale_product_domain()
        search = request.params.get('search', False)
        if search:
            values = {'user_id': self.env.user.id,
                      'date': fields.Datetime.now(),
                      'word': search}
            self.env['website.user.search'].sudo().create(values)

        return domain
