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

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import   Warning, RedirectWarning


class product_category(models.Model):
    _inherit = 'product.category'
    
    sequence_id = fields.Many2one('ir.sequence', string='Code Sequence')



class product_template(models.Model):
    _inherit = 'product.template'

    default_code = fields.Char(default='/')
     
    
    # doto de adaugat o constingere ca default_code si active sa fie unic

    @api.multi
    def button_new_code(self):
        self.ensure_one()
        if not self.default_code or self.default_code == '/' or self.default_code == 'auto':
            if self.categ_id.sequence_id:
                default_code =  self.env['ir.sequence'].next_by_id( self.categ_id.sequence_id.id  )
                self.write({'default_code':default_code})



class product_product(models.Model):
    _inherit = 'product.product'


    @api.multi
    def button_new_code(self):
        self.ensure_one()
        if not self.default_code or self.default_code == '/' or self.default_code == 'auto':
            if self.categ_id.sequence_id:
                default_code =  self.env['ir.sequence'].next_by_id( self.categ_id.sequence_id.id  )
                self.write({'default_code':default_code})

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: