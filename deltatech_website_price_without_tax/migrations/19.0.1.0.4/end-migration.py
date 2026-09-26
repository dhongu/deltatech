# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Reactivează view-ul generic dezactivat în pre-migration, după ce arhitectura lui a fost
    înlocuită cu cea din fișier. La update, loader-ul nu rescrie câmpul `active`."""
    cr.execute(SQL("SELECT to_regclass('deltatech_pwt_reactivate')"))
    if not cr.fetchone()[0]:
        return

    cr.execute(
        SQL(
            """
            UPDATE ir_ui_view SET active = true
            WHERE id IN (SELECT view_id FROM deltatech_pwt_reactivate)
            """
        )
    )
    _logger.info("Reactivated %s view(s) deactivated in pre-migration", cr.rowcount)
    cr.execute(SQL("DROP TABLE deltatech_pwt_reactivate"))
