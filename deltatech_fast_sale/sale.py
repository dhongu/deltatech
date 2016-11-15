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



from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp


class sale_order(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_button_confirm_to_invoice(self):
        if self.state == 'draft':
            self.action_confirm()  # confirma comanda

        for picking in self.picking_ids:
            picking.action_assign()  # verifica disponibilitate
            if not all(move.state == 'assigned' for move in picking.move_lines):
                raise Warning(_('Not all products are available.'))
            for pack in picking.pack_operation_ids:
                if pack.product_qty > 0 and pack.qty_done == 0:
                    pack.write({'qty_done': pack.product_qty})
                else:
                    pack.unlink()
            picking.do_transfer()

        action_obj = self.env.ref('sale.action_view_sale_advance_payment_inv')
        action = action_obj.read()[0]

        return action

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
