# -*- coding: utf-8 -*-




from odoo.exceptions import UserError, RedirectWarning
from odoo import models, fields, api, _
from odoo.tools.translate import _
from odoo import SUPERUSER_ID, api
import odoo.addons.decimal_precision as dp


class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"  
     

    expenses_deduction_id = fields.Many2one('deltatech.expenses.deduction')
    

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
