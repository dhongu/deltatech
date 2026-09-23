# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details
"""payment_amount / payment_status / provider_id become stored again.

Create the columns before ``_auto_init`` so the registry finds them and does not
queue a recompute of every sale order during module loading; the values are
computed in batches by the post-migration. On a database coming from 18.0 the
columns already exist (stored there) and are simply recomputed.
"""

from odoo.tools import SQL


def migrate(cr, version):
    cr.execute(
        SQL(
            """
            ALTER TABLE sale_order
                ADD COLUMN IF NOT EXISTS payment_amount numeric,
                ADD COLUMN IF NOT EXISTS payment_status varchar,
                ADD COLUMN IF NOT EXISTS provider_id int4
            """
        )
    )
