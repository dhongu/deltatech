# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """`gln` becomes a related field on the standard GLN (`global_location_number`,
    module `account_add_gln`), without its own column.

    Copy `gln` into the standard field where the standard one is empty. When
    both are set and differ, the standard value is kept and the partner is
    logged, so the right value can be decided by hand.
    """
    columns = {}
    for column in ("gln", "global_location_number"):
        cr.execute(
            SQL(
                "SELECT 1 FROM information_schema.columns WHERE table_name = 'res_partner' AND column_name = %s",
                column,
            )
        )
        columns[column] = bool(cr.fetchone())
    if not columns["gln"] or not columns["global_location_number"]:
        _logger.info("deltatech_gln: no `gln` column or no standard GLN column, nothing to copy.")
        return

    cr.execute(
        SQL(
            """
            UPDATE res_partner
               SET global_location_number = btrim(gln)
             WHERE btrim(coalesce(gln, '')) <> ''
               AND btrim(coalesce(global_location_number, '')) = ''
            """
        )
    )
    _logger.info("deltatech_gln: GLN copied to the standard field for %s partner(s).", cr.rowcount)

    cr.execute(
        SQL(
            """
            SELECT id, name, gln, global_location_number
              FROM res_partner
             WHERE btrim(coalesce(gln, '')) <> ''
               AND btrim(coalesce(global_location_number, '')) <> ''
               AND btrim(gln) <> btrim(global_location_number)
             ORDER BY id
            """
        )
    )
    for partner_id, name, gln, standard in cr.fetchall():
        _logger.warning(
            "deltatech_gln: partner %s (id %s) has GLN %s in `gln` and %s in the standard field; "
            "the standard value is kept.",
            name,
            partner_id,
            gln,
            standard,
        )
