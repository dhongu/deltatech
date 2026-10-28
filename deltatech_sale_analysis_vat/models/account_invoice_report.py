# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models
from odoo.tools import SQL


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    vat_tax_id = fields.Many2one("account.tax", string="VAT", readonly=True)
    vat_tax_group_id = fields.Many2one("account.tax.group", string="VAT Rate", readonly=True)
    is_fiscal_receipt = fields.Boolean(
        string="Invoice for Fiscal Receipt",
        readonly=True,
        help="Invoice issued for an existing fiscal receipt (Point of Sale order).",
    )

    def _select_list(self, table):
        # Only percentage taxes are considered VAT; fixed taxes (green tax, deposit
        # return scheme) are excluded so that each line keeps a single VAT rate.
        vat_alias = table._make_alias("vat")
        table._query.add_join(
            "LEFT JOIN",
            vat_alias,
            SQL(
                """(
                    SELECT DISTINCT ON (rel.account_move_line_id)
                        rel.account_move_line_id,
                        tax.id AS tax_id,
                        tax.tax_group_id AS tax_group_id
                    FROM account_move_line_account_tax_rel rel
                        JOIN account_tax tax ON tax.id = rel.account_tax_id
                    WHERE tax.amount_type = 'percent'
                    ORDER BY rel.account_move_line_id, tax.sequence, tax.id
                )"""
            ),
            SQL("%s = %s", vat_alias.account_move_line_id, table.id),
        )
        return super()._select_list(table) + [
            SQL("%s AS vat_tax_id", vat_alias.tax_id),
            SQL("%s AS vat_tax_group_id", vat_alias.tax_group_id),
            SQL(
                "EXISTS (SELECT 1 FROM pos_order po WHERE po.account_move = %s) AS is_fiscal_receipt",
                table.move_id,
            ),
        ]
