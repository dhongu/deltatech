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
from odoo.exceptions import   Warning, RedirectWarning



class product_template(models.Model):
    _inherit = 'product.template'

    percent_domain = fields.Char(string='Domain for Percent', default="[]" )
    percent_not_in = fields.Boolean('Not In')
    percent_product_list = fields.Many2many('product.product') 



    @api.onchange('percent_product_list','percent_not_in')
    def on_percent_product_list(self):
        if self.percent_product_list:
            if self.percent_not_in:
                self.percent_domain = "[('product_id','not in',%s)]" % self.percent_product_list.ids
            else:
                self.percent_domain = "[('product_id','in',%s)]" % self.percent_product_list.ids
        
        

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: