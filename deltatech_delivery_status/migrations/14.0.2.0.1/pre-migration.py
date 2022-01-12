# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    cr.execute(
        """
         ALTER TABLE stock_picking ADD COLUMN IF NOT EXISTS available_state VARCHAR;
    """
    )
