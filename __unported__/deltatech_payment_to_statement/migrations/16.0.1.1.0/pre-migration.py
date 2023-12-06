# ©  2023 Deltatech
# See README.rst file on addons root folder for license details
import logging

from openupgradelib import openupgrade
from psycopg2.errors import DatabaseError

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not openupgrade.column_exists(cr, "account_journal", "l10n_ro_journal_sequence_id"):
        if openupgrade.column_exists(cr, "account_journal", "journal_sequence_id"):
            try:
                cr.execute(
                    "ALTER TABLE account_journal RENAME COLUMN journal_sequence_id to l10n_ro_journal_sequence_id "
                )
            except DatabaseError as e:
                _logger.debug(e)
