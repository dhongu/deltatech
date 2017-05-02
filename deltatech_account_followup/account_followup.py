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
                          'picking_warn_msg': followup_partner.max_followup_id.block_message
                          }
                followup_partner.partner_id.write(values)
        res = super(account_followup_print, self).process_partners(partner_ids, data)
        return res


""""
class res_partner(models.Model):
    _inherit = "res.partner"

    latest_followup_date = fields.Date(compute='_compute_latest')
    latest_followup_level_id = fields.Many2one('account_followup.followup.line', compute='_compute_latest')
    latest_followup_level_id_without_lit = fields.Many2one('account_followup.followup.line', compute='_compute_latest')
    # clemency_days = fields.Integer(string="Clemency Days")


    @api.multi
    def _compute_latest(self):
        company = self.env.user.company_id
        for partner in self:
            amls = partner.unreconciled_aml_ids
            latest_date = False
            latest_level = False
            latest_days = False
            latest_level_without_lit = False
            latest_days_without_lit = False

            for aml in amls:
                delay_days = aml.followup_line_id.delay + partner.clemency_days
                if (aml.company_id == company):
                    if (aml.followup_line_id != False) and (not latest_days or latest_days < delay_days):
                        latest_days = delay_days
                        latest_level = aml.followup_line_id.id
                    if (not latest_date or latest_date < aml.followup_date):
                        latest_date = aml.followup_date
                    if (aml.blocked == False) and (aml.followup_line_id != False and (
                                not latest_days_without_lit or latest_days_without_lit < delay_days)):
                        latest_days_without_lit = delay_days
                        latest_level_without_lit = aml.followup_line_id.id

            partner.latest_followup_date = latest_date
            partner.latest_followup_level_id = latest_level,
            partner.latest_followup_level_id_without_lit = latest_level_without_lit
"""
