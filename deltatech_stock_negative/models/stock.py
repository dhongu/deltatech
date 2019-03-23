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
from odoo.exceptions import UserError, RedirectWarning



class stock_quant(models.Model):
    _inherit = "stock.quant"


    @api.model
    def _update_available_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, in_date=None):

        if location_id.usage == 'internal':
            if location_id.company_id.no_negative_stock:
                raise UserError(_('You have chosen to avoid negative stock. \
                        %s pieces of %s are remaining in location %s  but you want to transfer  \
                        %s pieces. Please adjust your quantities or \
                        correct your stock with an inventory adjustment.')% \
                        (product_id.qty_available, product_id.name, location_id.name, quantity))


        return super(stock_quant,self)._update_available_quantity( product_id, location_id, quantity, lot_id, package_id, owner_id,in_date)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
