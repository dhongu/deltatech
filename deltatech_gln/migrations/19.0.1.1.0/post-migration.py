# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Hand this module's `gln` values over to the standard field.

    Odoo now ships the same data as `res.partner.global_location_number`
    (module `account_add_gln`, auto-installed with `account`), so this module's
    `gln` is on its way out. Until it is removed, the two fields drift: on a
    real database only part of the partners had been copied over by hand, and
    the ones left behind were the commercial entities — the parent companies
    that carry the customer references — so anything reading the standard field
    silently saw a partner without a GLN.

    Only empty target values are filled: a value already in the standard field
    is never overwritten, so this is safe to re-run and cannot lose a
    correction made on the standard side.
    """
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
         WHERE table_name = 'res_partner' AND column_name = 'global_location_number'
        """
    )
    if not cr.fetchone():
        # `account_add_gln` is not installed (no `account` on this database):
        # there is no standard field to hand the values over to.
        _logger.info("deltatech_gln: standard field global_location_number absent, nothing to consolidate.")
        return

    cr.execute(
        """
        UPDATE res_partner
           SET global_location_number = gln
         WHERE gln IS NOT NULL
           AND gln <> ''
           AND (global_location_number IS NULL OR global_location_number = '')
        """
    )
    filled = cr.rowcount

    cr.execute(
        """
        SELECT count(*) FROM res_partner
         WHERE gln IS NOT NULL AND gln <> ''
           AND global_location_number IS NOT NULL AND global_location_number <> ''
           AND btrim(gln) <> btrim(global_location_number)
        """
    )
    conflicts = cr.fetchone()[0]

    _logger.info("deltatech_gln: %s partner(s) got their GLN copied to the standard field.", filled)
    if conflicts:
        _logger.warning(
            "deltatech_gln: %s partner(s) hold a different value in `gln` and in "
            "`global_location_number`. The standard field was left untouched for them — "
            "decide which value is right before this module is removed.",
            conflicts,
        )
