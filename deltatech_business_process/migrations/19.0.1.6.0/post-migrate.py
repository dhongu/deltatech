# ©  2023 Deltatech
# See README.rst file on addons root folder for license details
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

# Former selection value -> XML id of the new stage record (created by the
# module's data file during this same upgrade).
STAGE_MAP = {
    "first_stage": "deltatech_business_process.implementation_stage_first",
    "second_stage": "deltatech_business_process.implementation_stage_second",
    "start": "deltatech_business_process.implementation_stage_start",
}


def migrate(cr, version):
    # Only run on upgrades of an existing install, not on fresh installs.
    if not version:
        return

    # The old Selection column must still exist (skip if already migrated).
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'business_process'
          AND column_name = 'implementation_stage'
        """
    )
    if not cr.fetchone():
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    for old_value, xmlid in STAGE_MAP.items():
        stage = env.ref(xmlid, raise_if_not_found=False)
        if not stage:
            _logger.warning("Implementation stage %s not found; skipping '%s'", xmlid, old_value)
            continue
        cr.execute(
            """
            UPDATE business_process
            SET implementation_stage_id = %s
            WHERE implementation_stage = %s
              AND implementation_stage_id IS NULL
            """,
            (stage.id, old_value),
        )
        _logger.info(
            "deltatech_business_process: migrated %s row(s) from implementation_stage='%s' to stage id %s",
            cr.rowcount,
            old_value,
            stage.id,
        )

    # Any custom/legacy values that were not in the default set: create a stage
    # per distinct value and link the rows, so no data is silently lost.
    cr.execute(
        """
        SELECT DISTINCT implementation_stage
        FROM business_process
        WHERE implementation_stage IS NOT NULL
          AND implementation_stage_id IS NULL
        """
    )
    leftover = [row[0] for row in cr.fetchall() if row[0]]
    stage_model = env["business.process.implementation.stage"]
    for value in leftover:
        stage = stage_model.create({"name": value})
        cr.execute(
            """
            UPDATE business_process
            SET implementation_stage_id = %s
            WHERE implementation_stage = %s
              AND implementation_stage_id IS NULL
            """,
            (stage.id, value),
        )
        _logger.info(
            "deltatech_business_process: migrated %s row(s) with custom implementation_stage='%s' to new stage id %s",
            cr.rowcount,
            value,
            stage.id,
        )
