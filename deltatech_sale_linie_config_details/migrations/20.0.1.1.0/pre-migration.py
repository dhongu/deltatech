# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

"""On 19.0 ``config_details`` was a text column (JSON or ``str()`` of a Python list).

On 20.0 it is a ``jsonb`` column. Left alone, the update would drop the text column and create an
empty one. The text is converted here, before the module loads: JSON first, then a Python literal
(never evaluated); a text that is neither is kept as a JSON string, so nothing is lost. A database
that already has the ``jsonb`` column (installed on 20.0) is not touched.
"""

import ast
import json
import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)


def parse_config_details(text):
    """Same reading as ``models.sale_order_line.parse_config_details`` (the module is not imported yet)."""
    try:
        return json.loads(text)
    except ValueError:
        try:
            return ast.literal_eval(text)
        except (ValueError, SyntaxError, MemoryError, RecursionError):
            return text


def migrate(cr, version):
    cr.execute(
        SQL(
            """
            SELECT data_type FROM information_schema.columns
             WHERE table_name = 'sale_order_line' AND column_name = 'config_details'
            """
        )
    )
    row = cr.fetchone()
    if not row or row[0] == "jsonb":
        return
    cr.execute(SQL("ALTER TABLE sale_order_line RENAME COLUMN config_details TO config_details_text"))
    cr.execute(SQL("ALTER TABLE sale_order_line ADD COLUMN config_details jsonb"))
    cr.execute(
        SQL(
            "SELECT id, config_details_text FROM sale_order_line "
            "WHERE config_details_text IS NOT NULL AND config_details_text != ''"
        )
    )
    rows = cr.fetchall()
    for line_id, text in rows:
        cr.execute(
            SQL(
                "UPDATE sale_order_line SET config_details = %s::jsonb WHERE id = %s",
                json.dumps(parse_config_details(text), default=str),
                line_id,
            )
        )
    cr.execute(SQL("ALTER TABLE sale_order_line DROP COLUMN config_details_text"))
    _logger.info("config_details: %s sale order lines converted from text to JSON", len(rows))
