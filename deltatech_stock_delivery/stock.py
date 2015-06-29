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

from openerp import models, fields, api,  SUPERUSER_ID
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT


import openerp.addons.decimal_precision as dp 

class stock_picking(models.Model):
    _inherit = 'stock.picking'

    notice = fields.Boolean(string='Is a notice', states={'done': [('readonly', True)], 
                                                          'cancel': [('readonly', True)]},
                            compute='_compute_notice', store = True)              

    @api.one
    @api.depends('invoice_state')
    def _compute_notice(self ):
        invoice_state = self.invoice_state
        self.notice = (invoice_state <> 'none')
        




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
