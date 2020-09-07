# -*- coding: utf-8 -*-
# ©  2008-2019 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

import time

from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import UserError

# mapping invoice type to journal type


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    @api.model
    def _default_journal(self):

        if self._context.get('default_journal_id', False):
            return self.env['account.journal'].browse(self._context.get('default_journal_id'))

        if not self._context.get('active_ids'):
            return False

        company_id = self._context.get('company_id', self.env.user.company_id.id)

        sale_obj = self.env['sale.order']
        order = sale_obj.browse(self._context.get('active_ids'))[0]

        generic_parnter = self.env.ref('deltatech_print_bf.partner_generic', raise_if_not_found=False)
        if generic_parnter == order.partner_id:
            domain = [
                ('type', '=', 'sale'),
                ('company_id', '=', company_id),
                ('code', '=', 'BF')
            ]
        else:
            domain = [
                ('type', '=', 'sale'),
                ('company_id', '=', company_id),
                ('code', '!=', 'BF')
            ]

        return self.env['account.journal'].search(domain, limit=1)

    journal_id = fields.Many2one('account.journal', string='Journal',
                                 default=_default_journal,
                                 domain="[('type', '=', 'sale')]")  # de adaugat si ('company_id', '=', company_id)

    @api.multi
    def create_invoices(self):
        new_self = self.with_context(default_journal_id=self.journal_id)
        return super(SaleAdvancePaymentInv, new_self).create_invoices()
