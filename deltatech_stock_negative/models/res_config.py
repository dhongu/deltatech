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
    
    no_negative_stock  = fields.Boolean(string='No negative stock',
                                        help='Allows you to prohibit negative stock quantities.')
 
        
class stock_config_settings(models.TransientModel):
    _inherit = 'stock.config.settings'
    
    
    no_negative_stock  = fields.Boolean(string='No negative stock',
                                        help='Allows you to prohibit negative stock quantities.')

    @api.multi
    def set_default_no_negative_stock(self):
        self.env['ir.values'].set_default( 'stock.config.settings', 'no_negative_stock', self.no_negative_stock)
        self.env.user.company_ids.write({'no_negative_stock': self.no_negative_stock})


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:





