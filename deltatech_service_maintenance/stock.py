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
#
##############################################################################


from openerp import models, fields, api, _
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools import float_compare
import openerp.addons.decimal_precision as dp


class stock_picking(models.Model):
    _inherit = "stock.picking"

    notification_id = fields.Many2one('service.notification', string='Notification', readonly=True)

    @api.model
    @api.returns('self', lambda value:value.id)
    def create(self, vals):
        notification_id = self.env.context.get('notification_id',False)
        if notification_id:
            vals['notification_id'] = notification_id
        picking = super(stock_picking, self).create(vals)

        if notification_id:
            notification =  self.env['service.notification'].browse(notification_id)
            notification.write({'piking_id': picking.id})
        return picking

    @api.multi
    def new_notification(self):
        self.ensure_one()
        context = {
            'default_partner_id': self.partner_id.id}

        if self.move_lines:

            context['default_item_ids'] = []

            for item in self.move_lines:
                value = {}
                value['product_id'] = item.product_id.id
                value['quantity'] = item.product_uom_qty
                context['default_item_ids'] += [(0, 0, value)]

        context['sale_order_id'] = self.id
        return {
            'name': _('Notification'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'service.notification',
            'view_id': False,
            'views': [[False, 'form']],
            'context': context,
            'type': 'ir.actions.act_window'
        }





        # todo:  raport cu piesele consumate pe fiecare echipament / contract - raportat cu numarul de pagini tiparite

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: