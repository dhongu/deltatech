# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    if not version:
        return

    cr.execute(
        """
        update stock_quant set last_inventory_date = inventory_date
        """
    )
