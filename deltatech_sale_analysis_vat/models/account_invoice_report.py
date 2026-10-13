# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import api, fields, models
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

    @api.model
    def _select(self) -> SQL:
        return SQL(
            "%s, %s",
            super()._select(),
            SQL(
                """
                vat.tax_id                                                  AS vat_tax_id,
                vat.tax_group_id                                            AS vat_tax_group_id,
                EXISTS (SELECT 1 FROM pos_order po WHERE po.account_move = move.id)
                                                                            AS is_fiscal_receipt
                """
            ),
        )

    @api.model
    def _from(self) -> SQL:
        # Only percentage taxes are considered VAT; fixed taxes (green tax, deposit
        # return scheme) are excluded so that each line keeps a single VAT rate.
        return SQL(
            "%s %s",
            super()._from(),
            SQL(
                """
                LEFT JOIN (
                    SELECT DISTINCT ON (rel.account_move_line_id)
                        rel.account_move_line_id,
                        tax.id                                              AS tax_id,
                        tax.tax_group_id                                     AS tax_group_id
                    FROM account_move_line_account_tax_rel rel
                        JOIN account_tax tax ON tax.id = rel.account_tax_id
                    WHERE tax.amount_type = 'percent'
                    ORDER BY rel.account_move_line_id, tax.sequence, tax.id
                ) vat ON vat.account_move_line_id = line.id
                """
            ),
        )
