# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
"""Split the packaging quantity of a product into a purchase one and a sale one.

Until this version ``packaging.product.material`` had a single ``qty``, used both
for vendor bills and for customer invoices. Products packed one way by the vendor
and another way on shipping could not be described.

The old quantity applied to both directions, so it is carried over to both new
columns — the module keeps computing exactly what it did before the upgrade, and
the customer only has to correct the direction that actually differs.

Runs in pre-migration so that the values are moved before the ORM drops ``qty``.
"""

import logging

from odoo.tools import SQL
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)

TABLE = "packaging_product_material"


def migrate(cr, version):
    if not version:
        return
    if not column_exists(cr, TABLE, "qty"):
        # already migrated (or a fresh install that never had the single column)
        return

    # `qty_sale` takes over the old column, keeping its values in place;
    # `qty_purchase` is created next to it with the same values.
    table = SQL.identifier(TABLE)
    cr.execute(SQL("ALTER TABLE %s RENAME COLUMN qty TO qty_sale", table))
    cr.execute(SQL("ALTER TABLE %s ADD COLUMN qty_purchase double precision", table))
    cr.execute(SQL("UPDATE %s SET qty_purchase = qty_sale", table))
    _logger.info(
        "deltatech_report_packaging: split qty into qty_purchase/qty_sale on %s packaging lines; "
        "both directions kept the previous quantity, review the products packed differently.",
        cr.rowcount,
    )
