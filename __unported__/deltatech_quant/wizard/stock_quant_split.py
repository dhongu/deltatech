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
from odoo.exceptions import except_orm, Warning, RedirectWarning
import odoo.addons.decimal_precision as dp


class stock_quant_split(models.TransientModel):
    _name = 'stock.quant.split'
    _description = "Stock Quant Split"

    parts = fields.Float(string="Parts")

    @api.model
    def default_get(self, fields):
        defaults = super(stock_quant_split, self).default_get(fields)
        active_id = self.env.context.get('active_id', False)
        if active_id:
            quant = self.env['stock.quant'].browse(active_id)
            defaults['parts'] = quant.qty
        return defaults

    @api.multi
    def do_split(self):
        active_id = self.env.context.get('active_id', False)

        if active_id:
            quant = self.env['stock.quant'].browse(active_id)

            part = quant.qty / self.parts

            while quant:
                quant = self.env['stock.quant']._quant_split(quant, part)


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
