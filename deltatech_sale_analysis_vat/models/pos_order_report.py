# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import fields, models


class PosOrderReport(models.Model):
    _inherit = "report.pos.order"

    vat_tax_id = fields.Many2one("account.tax", string="VAT", readonly=True)
    vat_tax_group_id = fields.Many2one("account.tax.group", string="VAT Rate", readonly=True)

    def _select(self):
        return (
            super()._select()
            + """
                , vat.tax_id AS vat_tax_id
                , vat.tax_group_id AS vat_tax_group_id
            """
        )

    def _from(self):
        # Only percentage taxes are considered VAT; fixed taxes (green tax, deposit
        # return scheme) are excluded so that each line keeps a single VAT rate.
        return (
            super()._from()
            + """
                LEFT JOIN (
                    SELECT DISTINCT ON (rel.pos_order_line_id)
                        rel.pos_order_line_id,
                        tax.id AS tax_id,
                        tax.tax_group_id AS tax_group_id
                    FROM account_tax_pos_order_line_rel rel
                        JOIN account_tax tax ON tax.id = rel.account_tax_id
                    WHERE tax.amount_type = 'percent'
                    ORDER BY rel.pos_order_line_id, tax.sequence, tax.id
                ) vat ON vat.pos_order_line_id = l.id
            """
        )
