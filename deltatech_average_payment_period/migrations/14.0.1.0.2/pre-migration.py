# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    cr.execute(
        """
         ALTER TABLE account_move_line ADD COLUMN IF NOT EXISTS payment_days_simple NUMERIC;
    """
    )
