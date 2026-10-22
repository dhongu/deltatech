# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details
"""Rename the product manufacturer field ``manufacturer`` to ``manufacturer_id``.

The Many2one was named without the ``_id`` suffix. The column of ``product_template``
is renamed in place, so the values are kept, and the field metadata (``ir.model.fields``,
its xmlid, saved filters, exports, custom views) follows the new name.

``odoo.upgrade.util.rename_field`` does all of that, including the ``product.product``
field inherited through ``_inherits``. Where the library is missing, the SQL fallback
renames the column and the field records, enough for the ORM not to drop the column.

Runs in pre-migration so that the column is renamed before the ORM creates
``manufacturer_id`` empty and drops ``manufacturer``.
"""

import logging

from odoo.tools import SQL
from odoo.tools.sql import column_exists

_logger = logging.getLogger(__name__)

OLD = "manufacturer"
NEW = "manufacturer_id"
MODULE = "deltatech_product_extension"
# account.invoice.report is a SQL view rebuilt by the module, it only needs the metadata
MODELS = ("product.template", "product.product", "account.invoice.report")


def _rename_metadata(cr, model):
    cr.execute(
        SQL(
            "UPDATE ir_model_fields SET name = %s WHERE model = %s AND name = %s",
            NEW,
            model,
            OLD,
        )
    )
    old_xmlid = "field_{}__{}".format(model.replace(".", "_"), OLD)
    new_xmlid = "field_{}__{}".format(model.replace(".", "_"), NEW)
    cr.execute(
        SQL(
            "UPDATE ir_model_data SET name = %s WHERE module = %s AND model = 'ir.model.fields' AND name = %s",
            new_xmlid,
            MODULE,
            old_xmlid,
        )
    )
    cr.execute(
        SQL(
            """
            UPDATE ir_exports_line l SET name = %s
              FROM ir_exports e
             WHERE l.export_id = e.id AND e.resource = %s AND l.name = %s
            """,
            NEW,
            model,
            OLD,
        )
    )


def migrate(cr, version):
    if not version:
        return
    if not column_exists(cr, "product_template", OLD) or column_exists(cr, "product_template", NEW):
        # already migrated
        return

    try:
        from odoo.upgrade import util
    except ImportError:
        util = None

    if util is not None:
        util.rename_field(cr, "product.template", OLD, NEW)
        if column_exists(cr, "product_template", OLD):
            raise RuntimeError(f"{MODULE}: util.rename_field did not rename product_template.{OLD}")
        # the report is not linked by _inherits, util does not reach it
        util.rename_field(cr, "account.invoice.report", OLD, NEW)
    else:
        _logger.info("%s: odoo.upgrade.util not available, using SQL fallback", MODULE)
        cr.execute(SQL("ALTER TABLE product_template RENAME COLUMN %s TO %s", SQL.identifier(OLD), SQL.identifier(NEW)))
        for model in MODELS:
            _rename_metadata(cr, model)

    _logger.info("%s: renamed product_template.%s to %s", MODULE, OLD, NEW)
