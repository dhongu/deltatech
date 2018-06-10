# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo import tools

class AccountMoveReport(models.Model):
    _name = "account.move.report"
    _description = "Account Move Report"
    _auto = False
    _order = 'date desc'


    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    date = fields.Date('Date', readonly=True)
    account_id = fields.Many2one('account.account', 'Account', readonly=True)
    debit = fields.Float("Debit", readonly=True)
    credit = fields.Float("Credit", readonly=True)
    quantity = fields.Float("Quantity", readonly=True)
    balance = fields.Float("Balance", readonly=True)
    journal_id = fields.Many2one('account.journal', 'Journal', readonly=True)
    categ_id = fields.Many2one('product.category', 'Category', readonly=True)
    manufacturer = fields.Many2one('res.partner', string='Manufacturer', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', readonly=True)


    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (
            SELECT min(ml.id) as id, 
             ml.product_id, ml.date,ml.account_id,
             sum( ml.debit) as debit, sum( ml.credit) as credit,
             sum( -1*ml.balance) as balance,
             sum( ml.quantity) as quantity,
             ml.journal_id, t.categ_id, t.manufacturer, ml.company_id
             
             FROM account_move_line as ml
             JOIN account_move as am on ml.move_id = am.id
                 JOIN product_product p ON ml.product_id = p.id
                 LEFT JOIN product_template t ON p.product_tmpl_id = t.id
            WHERE tax_line_id is null
            GROUP BY  
             ml.product_id, ml.date, ml.account_id, ml.journal_id,
             t.categ_id, t.manufacturer, ml.company_id
            )
                        
        """ % self._table)

