# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """The new settlement mode is created as Cash on every deduction, but the payment journal could
    already be a bank or card journal: those deductions are settled by bank transfer, otherwise an
    advanced one could no longer be validated (cash mode needs a cash journal and the mode and journal
    are locked after the advance)."""
    if not version:
        return
    cr.execute(
        SQL(
            """
            UPDATE deltatech_expenses_deduction deduction
               SET settlement_mode = 'transfer'
              FROM account_journal journal
             WHERE journal.id = deduction.journal_id
               AND journal.type IN ('bank', 'credit')
               AND deduction.settlement_mode = 'cash'
            """
        )
    )
    _logger.info("deltatech_expenses: %s deconturi pe jurnal de bancă trecute pe virament", cr.rowcount)
