# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


def migrate(cr, version):
    # Up to 18.0 every customer invoice generated the delivery: keep that behaviour for the sale journals
    if not version:
        return
    cr.execute("UPDATE account_journal SET invoice_delivery = TRUE WHERE type = 'sale'")
