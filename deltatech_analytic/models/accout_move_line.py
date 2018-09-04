# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
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

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning, RedirectWarning
from openerp import tools


class account_move_line(models.Model):
    _inherit = "account.move.line"

    @api.model
    def _prepare_analytic_line(self, obj_line):
        res = super(account_move_line, self)._prepare_analytic_line(obj_line)
        if obj_line.invoice and obj_line.invoice.date_due:
            res['date_maturity'] = obj_line.invoice.date_due
        else:
            res['date_maturity'] = obj_line.date

        return res
