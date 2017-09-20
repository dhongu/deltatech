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

from odoo import api
from odoo import models


class mrp_production(models.Model):
    _inherit = 'mrp.production'

    @api.multi
    def action_assign(self):

        for production in self:
            dummy_id = 1 # self.env.ref('mrp.mrp_dummy_bom_line').id or 1

            new_move = production.move_raw_ids.filtered(lambda x: x.state == 'draft')
            for move in new_move:
                move.write({'location_dest_id': move.product_id.property_stock_production.id,
                            'unit_factor': 1.0,
                            'bom_line_id': dummy_id,
                            'state': 'confirmed'})
            new_move.action_assign()
        super(mrp_production, self).action_assign()
        return True

    """
    @api.onchange('move_raw_ids')
    def onchange_move_raw_product_id(self):
        for raw in self.move_raw_ids:
            raw.location_dest_id = raw.product_id.property_stock_production
            if raw.state == 'draft':
                raw.state = 'confirmed'
            if not raw.unit_factor:
                raw.unit_factor = 1.0
    """
