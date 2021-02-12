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
##############################################################################

from openerp import models, fields, api, _

import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning, RedirectWarning


class followup_line(models.Model):
    _inherit = 'account_followup.followup.line'

    block_partner = fields.Boolean(string="Block partner", default=False)
    block_message = fields.Text(string="Block partner message")


class account_followup_print(models.TransientModel):
    _inherit = 'account_followup.print'

    @api.model
    def process_partners(self, partner_ids, data):

        for followup_partner in self.env['account_followup.stat.by.partner'].browse(partner_ids):
            if followup_partner.max_followup_id.block_partner:
                values = {'invoice_warn': 'block',
                          'invoice_warn_msg': followup_partner.max_followup_id.block_message,
                          'sale_warn': 'block',
                          'sale_warn_msg': followup_partner.max_followup_id.block_message,
                          'picking_warn': 'block',
                          'picking_warn_msg': followup_partner.max_followup_id.block_message}
                followup_partner.partner_id.write(values)
        res = super(account_followup_print, self).process_partners(partner_ids, data)
        return res
