# ©  2008-2021 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo import fields, models


class PosBoxOut(models.TransientModel):
    _inherit = "cash.box.out"

    counterpart_account_id = fields.Many2one("account.account", string="Account")

    def default_get(self, fields_list):
        defaults = super(PosBoxOut, self).default_get(fields_list)

        return defaults

    def _calculate_values_for_statement_line(self, record):
        values = super(PosBoxOut, self)._calculate_values_for_statement_line(record=record)

        if self.counterpart_account_id:
            values["counterpart_account_id"] = self.counterpart_account_id.id

        return values
