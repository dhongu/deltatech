# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """EXPENSES-002: line currency is now the company currency of the deduction. Existing lines with
    another currency only had a wrong label (their amount was already added and posted as company
    currency), so only the currency is aligned, the amounts are kept."""
    if not version:
        return
    cr.execute(
        SQL(
            """
            UPDATE deltatech_expenses_deduction_line line
               SET currency_id = company.currency_id
              FROM deltatech_expenses_deduction deduction
              JOIN res_company company ON company.id = deduction.company_id
             WHERE line.expenses_deduction_id = deduction.id
               AND line.currency_id IS DISTINCT FROM company.currency_id
            """
        )
    )
    _logger.info("deltatech_expenses: %s linii de decont aduse la moneda companiei", cr.rowcount)
