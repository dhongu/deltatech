# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo.tools import SQL
from odoo.tools.parse_version import parse_version

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """The option "Advance and Settlement via Bank Statement / Cash Register" moves from the company to
    the journal: on a company that had it, it is set on every cash / bank / card journal, and the expense
    reports of that company keep the variant they were created with.

    The option existed on the company only in 19.0.3.10.0, and 19.0.3.11.0 already moved it: a database
    coming from 19.0 at 19.0.3.11.0 or later is skipped, so journals unticked since then stay unticked.
    A database already on 20.0 never had the company column and is skipped by the column check."""
    if not version:
        return
    if version.startswith("19.0.") and parse_version(version) >= parse_version("19.0.3.11.0"):
        return
    cr.execute(
        SQL(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'res_company' AND column_name = 'expenses_no_payment_moves'"
        )
    )
    if not cr.fetchone():
        return
    cr.execute(
        SQL(
            """
            UPDATE account_journal journal
               SET expenses_no_payment_moves = TRUE
              FROM res_company company
             WHERE company.id = journal.company_id
               AND company.expenses_no_payment_moves
               AND journal.type IN ('cash', 'bank', 'credit')
            """
        )
    )
    _logger.info("deltatech_expenses: bifa extras/casă pusă pe %s jurnale", cr.rowcount)
    cr.execute(
        SQL(
            """
            UPDATE deltatech_expenses_deduction deduction
               SET no_payment_moves = TRUE
              FROM res_company company
             WHERE company.id = deduction.company_id
               AND company.expenses_no_payment_moves
            """
        )
    )
    _logger.info("deltatech_expenses: %s deconturi păstrează varianta fără note de plată", cr.rowcount)
