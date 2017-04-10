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
from odoo.tools import float_compare
import odoo.addons.decimal_precision as dp
from datetime import datetime, date, timedelta
from dateutil.relativedelta import relativedelta


class mrp_production_start(models.TransientModel):
    _name = 'mrp.production.start'
    _description = "Start Production"

    scanned_barcode = fields.Char(string="Scanned Bar code")
    production_ids = fields.Many2many('mrp.production', string='Production Order')

    @api.onchange('scanned_barcode')
    def onchange_scanned_barcode(self):
        scanned_barcode = self.scanned_barcode
        # if not scanned_barcode or len(scanned_barcode)<>13:
        #    self.scanned_barcode = ''
        #    return {}

        domain = [('name', '=', self.scanned_barcode)]
        res = self.env['mrp.production'].search(domain)
        if res:
            production_ids = self._fields['production_ids'].convert_to_onchange(self._cache['production_ids'])

            for production_id in res:
                production_ids.append([4, production_id.id, 0])

            production_ids = self._convert_to_cache({'production_ids': production_ids}, validate=False)

            self.update(production_ids)
            self.scanned_barcode = ''

    @api.model
    def default_get(self, fields):
        defaults = super(mrp_production_start, self).default_get(fields)

        active_ids = self.env.context.get('active_ids', False)

        domain = [('id', 'in', active_ids)]
        res = self.env['mrp.production'].search(domain)
        defaults['production_ids'] = [(6, 0, [rec.id for rec in res])]
        return defaults

    @api.multi
    def do_start(self):
        for production in self.production_ids:
            if production.state == 'confirmed':
                production.button_plan()


        action = self.env.ref('mrp.mrp_production_action').read()[0]
        action['domain'] = "[('id','in', [" + ','.join(map(str, self.production_ids.ids)) + "])]"
        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
