# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Deltatech All Rights Reserved
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





class stock_quant(models.Model):
    _inherit = "stock.quant"


    @api.model
    def _quant_create_from_move(self, qty, move, lot_id=False, owner_id=False,
                                src_package_id=False, dest_package_id=False,
                                force_location_from=False, force_location_to=False):

        if move.location_id.usage == 'internal':
            if move.location_id.company_id.no_negative_stock:
                raise Warning(_('You have chosen to avoid negative stock. \
                        %s pieces of %s are remaining in location %s  but you want to transfer  \
                        %s pieces. Please adjust your quantities or \
                        correct your stock with an inventory adjustment.')% \
                        (move.product_id.qty_available, move.product_id.name, move.location_id.name, move.product_uom_qty))

        quant = super(stock_quant, self)._quant_create_from_move( qty, move, lot_id=lot_id, owner_id=owner_id,
                                 src_package_id=src_package_id, dest_package_id=dest_package_id,
                                 force_location_from=force_location_from, force_location_to=force_location_to)

        return quant
 
 


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
