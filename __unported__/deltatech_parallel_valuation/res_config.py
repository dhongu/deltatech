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

from odoo import models, fields, api, tools, _
from odoo.exceptions import except_orm, Warning, RedirectWarning


class res_company(models.Model):
    _inherit = 'res.company'
    _name = 'res.company'
    parallel_currency_id = fields.Many2one('res.currency',
                                           string='Parallel company currency', help="Parallel currency of the company.",
                                           default=lambda self: self.env.ref('base.RON'))


class account_config_settings(models.TransientModel):
    _inherit = 'account.config.settings'
    _name = 'account.config.settings'
    parallel_currency_id = fields.Many2one('res.currency', related='company_id.parallel_currency_id',
                                           string='Parallel company currency', help="Parallel currency of the company.")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
