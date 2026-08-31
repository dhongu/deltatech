# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
"""Take over the records of deltatech_generic_partner_restriction.

That module was merged into this one and is now an empty transition shim.
Its ``ir_model_data`` rows must change owner *before* the shim is updated,
otherwise Odoo cleans up the records that are no longer declared by it and
drops the ``account_journal.restriction`` column together with the journals
the customer had ticked.

Runs first because the shim depends on this module, so this module is loaded
(and migrated) before it.
"""

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)

OLD_MODULE = "deltatech_generic_partner_restriction"
NEW_MODULE = "deltatech_partner_generic"

# The xml ids kept the same names in the merged module, so a plain rename of
# the owning module is enough.
MOVED_XML_IDS = (
    "field_account_journal__restriction",
    "account_journal_view_list",
    "account_journal_view_form",
)


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        SQL(
            """
            UPDATE ir_model_data d
               SET module = %s
             WHERE d.module = %s
               AND d.name IN %s
               AND NOT EXISTS (
                     SELECT 1
                       FROM ir_model_data other
                      WHERE other.module = %s
                        AND other.name = d.name
                   )
            """,
            NEW_MODULE,
            OLD_MODULE,
            MOVED_XML_IDS,
            NEW_MODULE,
        )
    )
    if cr.rowcount:
        _logger.info("Moved %s records from %s to %s", cr.rowcount, OLD_MODULE, NEW_MODULE)
