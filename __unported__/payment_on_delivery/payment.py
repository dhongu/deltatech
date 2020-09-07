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


class OnDeliveryPaymentAcquirer(models.Model):
    _inherit = 'payment.acquirer'

    partner_id = fields.Many2one('res.partner', string='Partner')
    account_debit = fields.Many2one('account.account', string='Debit Account')

    def _get_providers(self, cr, uid, context=None):
        providers = super(OnDeliveryPaymentAcquirer, self)._get_providers(cr, uid, context=context)
        providers.append(['on_delivery', _('Cash On Delivery')])
        return providers

    def on_delivery_get_form_action_url(self, cr, uid, id, context=None):
        return '/payment/on_delivery/feedback'


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
