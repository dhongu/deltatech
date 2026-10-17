# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details
"""The obsolete ``terrabit_product_labels`` is replaced by this module.

On 18.0 it was an empty bridge that only depended on this module, and it was not
migrated to 19.0. A database that still has it installed reports it as a module
with an inconsistent state; it is marked uninstalled here, there is nothing of its
own to keep.
"""

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)

OLD_MODULE = "terrabit_product_labels"


def migrate(cr, version):
    cr.execute(
        SQL(
            "UPDATE ir_module_module SET state = 'uninstalled' WHERE name = %s AND state != 'uninstalled'",
            OLD_MODULE,
        )
    )
    if cr.rowcount:
        _logger.info("Obsolete module %s replaced by deltatech_product_labels", OLD_MODULE)
