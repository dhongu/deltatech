# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """The deduction currency is now stored and follows the cash journal currency. Existing deductions
    were kept and posted in the company currency, so they keep it instead of being recomputed from
    the journal."""
    if not version:
        return
    cr.execute(SQL("ALTER TABLE deltatech_expenses_deduction ADD COLUMN IF NOT EXISTS currency_id integer"))
    cr.execute(
        SQL(
            """
            UPDATE deltatech_expenses_deduction deduction
               SET currency_id = company.currency_id
              FROM res_company company
             WHERE company.id = deduction.company_id
               AND deduction.currency_id IS NULL
            """
        )
    )
    _logger.info("deltatech_expenses: %s deconturi păstrate în moneda companiei", cr.rowcount)
