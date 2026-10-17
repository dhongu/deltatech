# ©  2008-2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.tools import SQL
from odoo.tools.sql import column_exists


def migrate(cr, version):
    # 19.0.1.1.0 had a Boolean "Inherit Category Icons"; it became the "inherit" level.
    if column_exists(cr, "website", "category_icon_inherit"):
        cr.execute(SQL("UPDATE website SET category_icon_levels = 'inherit' WHERE category_icon_inherit"))
        cr.execute(SQL("ALTER TABLE website DROP COLUMN category_icon_inherit"))
