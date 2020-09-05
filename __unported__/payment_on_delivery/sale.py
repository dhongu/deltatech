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
#
##############################################################################


from odoo import models, fields, api, _
from odoo.exceptions import except_orm, Warning, RedirectWarning
from odoo.tools import float_compare


class sale_order(models.Model):
    _inherit = "sale.order"

    # cmpurile sunt in modulul website_sale
    #payment_acquirer_id = fields.Many2one('payment.acquirer', string='Payment Acquirer', on_delete='set null', copy=False)
    #payment_tx_id = fields.Many2one('payment.transaction', string='Transaction', on_delete='set null', copy=False)

    @api.model
    def _prepare_invoice(self, order, lines, context=None):

        if context is None:
            context = {}
        if order.payment_acquirer_id:
            context['default_payment_acquirer_id'] = order.payment_acquirer_id.id
        res = super(sale_order, self)._prepare_invoice(cr, uid, order, lines, context)

        return res

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
