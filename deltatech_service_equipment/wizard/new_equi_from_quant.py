# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2017 Deltatech All Rights Reserved
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
#
##############################################################################

from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
import openerp.addons.decimal_precision as dp
from openerp.api import Environment
import threading


class service_equi_from_quant(models.TransientModel):
    _name = 'service.equi.from.quant'
    _description = "Equipment From Quants"

    type_id = fields.Many2one('service.equipment.type', required=True, string='Type')
    quant_ids = fields.Many2many('stock.quant', 'service_equi_from_quants', 'wizard_id', 'quant_id', string='Quants')

    @api.model
    def default_get(self, fields):
        defaults = super(service_equi_from_quant, self).default_get(fields)

        active_ids = self.env.context.get('active_ids', False)

        # daca deja exista echipamente 
        equipments = self.env['service.equipment'].search([('quant_id', 'in', active_ids)])
        for equipment in equipments:
            active_ids.remove(equipment.quant_id.id)

        quants = self.env['stock.quant'].search([('id', 'in', active_ids)])

        defaults['quant_ids'] = [(6, 0, [quant.id for quant in quants])]
        return defaults

    @api.multi
    def do_create_equi(self):

        equipments = self.env['service.equipment']
        for quant in self.quant_ids:
            equipment = self.env['service.equipment'].create({
                'type_id': self.type_id.id,
                'quant_id': quant.id
            })
            equipments.create_meters_button()
            equipments |= equipment

        # si instalare

        return {
            'domain': "[('id','in', [" + ','.join(map(str, equipments.ids)) + "])]",
            'name': _('Equipmente'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'service.equipment',
            'view_id': False,
            'type': 'ir.actions.act_window'
        }
