# -*- coding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2018 Deltatech All Rights Reserved
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
from openerp import models, fields, api, _


class stock_invoice_onshipping(models.TransientModel):
    _inherit = "stock.invoice.onshipping"

    @api.model
    def default_get(self, fields):
        res = super(stock_invoice_onshipping, self).default_get(fields)
        journal_type = self._get_journal_type()
        journals = self.env['account.journal'].search([('type', '=', journal_type)])

        active_id = self.env.context['active_id']
        active_picking = self.env['stock.picking'].browse(active_id)

        if journal_type == 'sale':
            generic_partner = eval( self.env['ir.config_parameter'].sudo().get_param(key="sale.generic_partner", default="False"))
            # is_company = active_picking.partner_id.is_company or active_picking.partner_id.parent_id.is_company
            if generic_partner and active_picking.partner_id.id in generic_partner:
                for journal in journals:
                    if journal.fiscal_receipt:
                        res['journal_id'] = journal.id

        return res
