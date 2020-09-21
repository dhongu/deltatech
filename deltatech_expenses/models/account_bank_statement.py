

from odoo import SUPERUSER_ID, _, api, fields, models
from odoo.exceptions import RedirectWarning, UserError
from odoo.tools.translate import _

import odoo.addons.decimal_precision as dp


class account_bank_statement_line(models.Model):
    _inherit = "account.bank.statement.line"

    expenses_deduction_id = fields.Many2one("deltatech.expenses.deduction")


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
