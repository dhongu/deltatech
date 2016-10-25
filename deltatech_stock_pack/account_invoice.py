# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2016 Deltatech All Rights Reserved
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


class account_invoice(models.Model):
    _inherit = "account.invoice"
    
    
    package_ids = fields.Many2many('stock.quant.package', 'invoice_packages', 'invoice_id', 'package_id', compute='_compute_package_ids')
    
    
    @api.model
    def _compute_package_ids(self):
        for invoice in self:
            package_ids = self.env['stock.quant.package']
            for picking in invoice.picking_ids:
                for move in picking.move_lines:
                    for quant in move.quant_ids:
                        package_ids |= quant.package_id
            invoice.package_ids = package_ids
                
                
                
                
                