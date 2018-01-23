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
from openerp import tools


class analytic_analyti_account(models.Model):
    _inherit = "account.analytic.account"

    project_amount = fields.Float()
    project_margin = fields.Float()


class analytic_entries_report(models.Model):
    _inherit = "analytic.entries.report"

    # categ_id = fields.Many2one('product.category', 'Internal Category', domain="[('type','=','normal')]")
    type = fields.Selection(
        [('view', 'Analytic View'), ('normal', 'Analytic Account'), ('contract', 'Contract or Project'),
         ('template', 'Template of Contract')], 'Type of Account')
    parent_id = fields.Many2one('account.analytic.account', 'Parent Analytic Account')
    journal_type = fields.Selection([('sale', 'Sale'), ('purchase', 'Purchase'),
                                     ('cash', 'Cash'), ('general', 'General'),
                                     ('situation', 'Situation')], string='Type')

    def init(self, cr):
        tools.drop_view_if_exists(cr, 'analytic_entries_report')
        cr.execute("""
            create or replace view analytic_entries_report as (
                 select
                     min(a.id) as id,
                     count(distinct a.id) as nbr,
                     a.date as date,
                     a.user_id as user_id,
                     a.name as name,
                     analytic.partner_id as partner_id,
                     a.company_id as company_id,
                     a.currency_id as currency_id,
                     a.account_id as account_id,
                     a.general_account_id as general_account_id,
                     a.journal_id as journal_id,
                     a.move_id as move_id,
                     a.product_id as product_id,
                     a.product_uom_id as product_uom_id,
                     sum(a.amount) as amount,
                     sum(a.unit_amount) as unit_amount,
                     analytic.type as type,
                     journal.type as journal_type,
                     analytic.parent_id as parent_id
                 from
                     account_analytic_line a
                     join account_analytic_account analytic on analytic.id = a.account_id
                     join account_analytic_journal journal on journal.id = a.journal_id

                 group by
                     a.date, a.user_id,a.name,analytic.partner_id,a.company_id,a.currency_id,
                     a.account_id,a.general_account_id,a.journal_id,
                     a.move_id,a.product_id,a.product_uom_id,
                     analytic.type, journal.type, analytic.parent_id
            )
        """)
