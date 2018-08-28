# -*- coding: utf-8 -*-
# ©  2015-2018 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models


class AccountFiscalPosition(models.Model):
    _inherit = 'account.fiscal.position'

    company_id = fields.Many2one('res.company',
                                 compute='_compute_company_id',
                                 inverse='_set_company_id',
                                 search='_search_company')
    store_company_id = fields.Many2one('res.company', string='Company', required=True,
                                       default=lambda self: self.env.user.company_id)

    @api.model
    def _search_company(self, operator, operand):
        account_rule = self.env.ref('account.account_comp_rule')
        company_share_account = not bool(account_rule.active)
        if company_share_account:
            domain = []
        else:
            domain = [('store_company_id', operator, operand)]
        return domain

    @api.multi
    def _compute_company_id(self):
        account_rule = self.env.ref('account.account_comp_rule')  # account.account_fiscal_position_comp_rule
        company_share_account = not bool(account_rule.active)
        for account in self:
            if not company_share_account:
                account.company_id = account.store_company_id
            else:
                account.company_id = self.env.user.company_id

    @api.multi
    def _set_company_id(self):
        for account in self:
            account.store_company_id = account.company_id


class AccountAccount(models.Model):
    _inherit = "account.account"

    company_id = fields.Many2one('res.company',
                                 compute='_compute_company_id',
                                 inverse='_set_company_id',
                                 search='_search_company')
    store_company_id = fields.Many2one('res.company', string='Company', required=True,
                                       default=lambda self: self.env.user.company_id)

    @api.model
    def _search_company(self, operator, operand):
        account_rule = self.env.ref('account.account_comp_rule')
        company_share_account = not bool(account_rule.active)
        if company_share_account:
            domain = []
        else:
            domain = [('store_company_id', operator, operand)]
        return domain

    @api.multi
    def _compute_company_id(self):
        account_rule = self.env.ref('account.account_comp_rule')
        company_share_account = not bool(account_rule.active)
        for account in self:
            if not company_share_account:
                account.company_id = account.store_company_id
            else:
                account.company_id = self.env.user.company_id

    @api.multi
    def _set_company_id(self):
        for account in self:
            account.store_company_id = account.company_id


class AccountTax(models.Model):
    _inherit = 'account.tax'

    color = fields.Integer(string='Color Index', default=0)

    company_id = fields.Many2one('res.company',
                                 compute='_compute_company_id',
                                 inverse='_set_company_id',
                                 search='_search_company')

    store_company_id = fields.Many2one('res.company', string='Company', required=True,
                                       default=lambda self: self.env.user.company_id)

    @api.model
    def _search_company(self, operator, operand):
        account_tax_rule = self.env.ref('account.tax_comp_rule')
        company_share_account_tax = not bool(account_tax_rule.active)
        if company_share_account_tax:
            domain = []
        else:
            domain = [('store_company_id', operator, operand)]
        return domain

    @api.multi
    def _compute_company_id(self):
        account_tax_rule = self.env.ref('account.tax_comp_rule')
        vat_subjected = self.env.user.company_id.partner_id.vat_subjected
        company_share_account_tax = not bool(account_tax_rule.active)
        for tax in self:
            if company_share_account_tax and vat_subjected:
                tax.company_id = self.env.user.company_id
            else:
                tax.company_id = tax.store_company_id


    @api.multi
    def _set_company_id(self):
        for tax in self:
            tax.store_company_id = tax.company_id
