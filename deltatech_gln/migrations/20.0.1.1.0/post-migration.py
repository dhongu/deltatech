# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

import json
import logging

from odoo import SUPERUSER_ID, api
from odoo.tools import SQL
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)

GLN_KEY = "EAN_GLN"


def migrate(cr, version):
    """Move this module's GLN values into the standard partner identifiers.

    Since 20.0 `res.partner.gln` is no longer stored: it is a proxy on
    `additional_identifiers["EAN_GLN"]` (module `base`), the same value that
    `account` exposes as `global_location_number`. The old `gln` column is left
    in place by the ORM; its values are copied into the JSON here.

    Sources, in order: the `gln` column, then the `global_location_number`
    column left over from 19.0 (`account_add_gln`), if still there.
    Rules:
    - an identifier already present in the JSON is never overwritten (safe to
      re-run, a correction made on the standard side is kept); partners with a
      different value are reported;
    - the standard refuses malformed GLNs (EAN check digit): such values are not
      copied, they stay in the old `gln` column and are reported, so they can be
      corrected by hand.
    """
    if not column_exists(cr, "res_partner", "gln"):
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    Partner = env["res.partner"]

    legacy_std = column_exists(cr, "res_partner", "global_location_number")
    cr.execute(
        SQL(
            """
            SELECT id,
                   NULLIF(btrim(gln), ''),
                   %(legacy)s,
                   additional_identifiers ->> %(key)s
              FROM res_partner
             WHERE NULLIF(btrim(gln), '') IS NOT NULL %(or_legacy)s
            """,
            legacy=SQL("NULLIF(btrim(global_location_number), '')") if legacy_std else SQL("NULL"),
            or_legacy=SQL("OR NULLIF(btrim(global_location_number), '') IS NOT NULL") if legacy_std else SQL(""),
            key=GLN_KEY,
        )
    )
    filled, conflicts, invalid = [], [], []
    for partner_id, gln, legacy_gln, current in cr.fetchall():
        value = gln or legacy_gln
        validation = Partner._validate_identifier(GLN_KEY, value)
        if not validation["valid"]:
            invalid.append((partner_id, value))
            continue
        normalized = validation["value"]
        if current:
            if current != normalized:
                conflicts.append(partner_id)
            continue
        cr.execute(
            SQL(
                """
                UPDATE res_partner
                   SET additional_identifiers = COALESCE(additional_identifiers, '{}'::jsonb) || %s::jsonb
                 WHERE id = %s
                """,
                json.dumps({GLN_KEY: normalized}),
                partner_id,
            )
        )
        filled.append(partner_id)

    Partner.invalidate_model(["additional_identifiers"])
    _logger.info("deltatech_gln: %s partner(s) got their GLN moved to the standard identifiers.", len(filled))
    if conflicts:
        _logger.warning(
            "deltatech_gln: %s partner(s) already had a different EAN/GLN in the standard identifiers, "
            "which was kept (ids: %s). The old value is still in the column res_partner.gln.",
            len(conflicts),
            conflicts[:50],
        )
    if invalid:
        _logger.warning(
            "deltatech_gln: %s partner(s) have a malformed GLN that the standard refuses; it was not "
            "migrated and stays only in the column res_partner.gln — correct it on the partner: %s",
            len(invalid),
            invalid[:50],
        )
