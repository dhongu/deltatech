# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_share_account = fields.Boolean(
        'Share chart of account to all companies',
        help="Share your chart of account to all companies defined in your instance.\n")
    company_share_account_tax = fields.Boolean('Share taxes account to all companies')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        account_rule = self.env.ref('account.account_comp_rule')
        res.update(
            company_share_account=not bool(account_rule.active),
        )
        account_tax_rule = self.env.ref('account.tax_comp_rule')
        res.update(
            company_share_account_tax=not bool(account_tax_rule.active),
        )

        return res

    def set_values(self):
        if self.chart_template_id and self.chart_template_id != self.company_id.chart_template_id:
            if self.company_share_account and not self.company_id.chart_template_id:
                company = self.env['res.company'].sudo().search([('chart_template_id', '!=', False)], limit=1)
                if company:
                    self.company_id.write({'chart_template_id': company.chart_template_id.id})
                    todo_list = [
                        'property_account_receivable_id',
                        'property_account_payable_id',
                        'property_account_expense_categ_id',
                        'property_account_income_categ_id',
                        'property_account_expense_id',
                        'property_account_income_id',
                        'property_stock_account_input_categ_id',
                        'property_stock_account_output_categ_id',
                        'property_stock_valuation_account_id',
                    ]
                    PropertyObj = self.env['ir.property']
                    for property in todo_list:
                        properties = PropertyObj.search([('name', '=', property),
                                                         ('company_id', '=', self.company_id.id)])
                        if not properties:
                            properties = PropertyObj.search([('name', '=', property),
                                                             ('company_id', '=', company.id)])
                            if properties:
                                for prop in properties:
                                    prop.copy({'company_id': self.company_id.id})

        super(ResConfigSettings, self).set_values()
        account_rule = self.env.ref('account.account_comp_rule')
        account_rule.write({'active': not bool(self.company_share_account)})
        account_tax_rule = self.env.ref('account.tax_comp_rule')
        account_tax_rule.write({'active': not bool(self.company_share_account_tax)})

    @api.depends('company_id')
    def _compute_has_chart_of_accounts(self):
        super(ResConfigSettings, self)._compute_has_chart_of_accounts()

        if self.company_share_account and not self.company_id.chart_template_id:
            company = self.env['res.company'].sudo().search([('chart_template_id', '!=', False)], limit=1)
            if company:
                self.has_chart_of_accounts = bool(company.chart_template_id)
                self.chart_template_id = company.chart_template_id
