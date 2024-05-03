# ©  2015-now Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from datetime import datetime

from odoo import _, models
from odoo.exceptions import UserError


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    def action_undo_reconciliation(self):
        get_param = self.env["ir.config_parameter"].sudo().get_param
        date_limit = get_param("sequence.mixin.constraint_start_date", "2000-01-01")
        if date_limit:
            date_limit_obj = datetime.strptime(date_limit, "%Y-%m-%d").date()
            for st_line in self:
                if st_line.date < date_limit_obj:
                    raise UserError(
                        _(
                            "You cannot perform this operation on this line (date restriction). "
                            "Please contact your support team."
                        )
                    )
        return super().action_undo_reconciliation()
