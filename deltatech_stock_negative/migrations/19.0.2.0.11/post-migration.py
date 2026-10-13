# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Load the corrected Romanian translations over the old ones.

    An upgrade loads the .po files without overwriting: the setting fixed in
    ro.po ("Fără stoc negativ", spelled "Fară" before) would keep its old
    wording on an existing database.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    env["ir.module.module"].search([("name", "=", "deltatech_stock_negative")])._update_translations(overwrite=True)
