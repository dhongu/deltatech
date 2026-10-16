# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    # Rack/Row/Shelf/Case are now shown only with "Show manual location fields".
    # Before, the setting had no effect and the fields were always visible: keep them
    # visible on existing databases by enabling the setting (it can be turned off).
    env = api.Environment(cr, SUPERUSER_ID, {})
    group = env.ref("deltatech_stock_inventory.group_show_manual_location_fields", raise_if_not_found=False)
    if group:
        env.ref("base.group_user").write({"implied_ids": [(4, group.id)]})
