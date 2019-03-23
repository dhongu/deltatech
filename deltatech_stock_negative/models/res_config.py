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
from odoo.exceptions import UserError, RedirectWarning


class res_company(models.Model):
    _inherit = 'res.company'

    no_negative_stock = fields.Boolean(string='No negative stock', default=True,
                                       help='Allows you to prohibit negative stock quantities.')


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    no_negative_stock = fields.Boolean(related='company_id.no_negative_stock',
                                       string='No negative stock', readonly=False,
                                       help='Allows you to prohibit negative stock quantities.')


    #
    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     res.update(
    #         no_negative_stock=self.env['ir.config_parameter'].sudo().get_param('stock.no_negative_stock')
    #     )
    #     return res
    #
    # @api.multi
    # def set_values(self):
    #     super(ResConfigSettings, self).set_values()
    #     if not self.user_has_groups('stock.group_stock_manager'):
    #         return
    #     self.env['ir.config_parameter'].sudo().set_param('stock.no_negative_stock', self.no_negative_stock)
    #     self.env.user.company_id.write({'no_negative_stock': self.no_negative_stock})
