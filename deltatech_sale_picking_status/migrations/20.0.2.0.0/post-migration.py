# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

import logging
import re

from odoo.tools import SQL

_logger = logging.getLogger(__name__)

IN_PROGRESS = "['pending', 'started', 'partial']"

# picking_status (done / in_progress) -> standard delivery_status
LEAF_MAP = {
    ("=", "done"): "('delivery_status', '=', 'full')",
    ("!=", "done"): "('delivery_status', '!=', 'full')",
    ("=", "in_progress"): f"('delivery_status', 'in', {IN_PROGRESS})",
    ("!=", "in_progress"): f"('delivery_status', 'not in', {IN_PROGRESS})",
}

LEAF_RE = re.compile(
    r"""[(\[]\s*['"]picking_status['"]\s*,\s*['"](=|==|!=)['"]\s*,\s*['"](done|in_progress)['"]\s*[)\]]"""
)
FIELD_RE = re.compile(r"""(['"])picking_status\1""")


def convert_domain(domain):
    """Rewrite the picking_status leaves of a domain (as text) on delivery_status."""

    def _leaf(match):
        operator = "=" if match.group(1) == "==" else match.group(1)
        return LEAF_MAP[(operator, match.group(2))]

    return LEAF_RE.sub(_leaf, domain)


def convert_field(text):
    """Rename picking_status to delivery_status in a group_by / sort text."""
    return FIELD_RE.sub(r"\1delivery_status\1", text)


def migrate(cr, version):
    """picking_status was replaced by the standard sale.order.delivery_status.

    The field values need no copy: delivery_status is stored and computed by
    sale_stock. What still points to picking_status is user data: favorite
    filters, export templates and views edited in the database.
    """
    if not version:
        return

    cr.execute(
        """
        SELECT id, domain, context, sort FROM ir_filters
         WHERE model_id = 'sale.order'
           AND (domain LIKE '%%picking_status%%' OR context LIKE '%%picking_status%%'
                OR sort LIKE '%%picking_status%%')
        """
    )
    for filter_id, domain, context, sort in cr.fetchall():
        new_domain = convert_domain(domain or "")
        new_context = convert_field(context or "")
        new_sort = convert_field(sort or "")
        cr.execute(
            SQL(
                "UPDATE ir_filters SET domain = %s, context = %s, sort = %s WHERE id = %s",
                new_domain or domain,
                new_context or context,
                new_sort or sort,
                filter_id,
            )
        )
        if "picking_status" in new_domain:
            _logger.warning(
                "Filter %s on sale.order still uses picking_status, rewrite it on delivery_status: %s",
                filter_id,
                new_domain,
            )

    cr.execute(
        """
        UPDATE ir_exports_line line SET name = 'delivery_status'
          FROM ir_exports export
         WHERE line.export_id = export.id
           AND export.resource = 'sale.order'
           AND line.name = 'picking_status'
        """
    )

    cr.execute(
        """
        SELECT view.id, view.name FROM ir_ui_view view
         WHERE view.model = 'sale.order'
           AND view.arch_db::text LIKE '%%picking_status%%'
           AND NOT EXISTS (
               SELECT 1 FROM ir_model_data imd
                WHERE imd.model = 'ir.ui.view' AND imd.res_id = view.id
                  AND imd.module = 'deltatech_sale_picking_status'
           )
        """
    )
    for view_id, view_name in cr.fetchall():
        _logger.warning(
            "View %s (%s) uses the removed field picking_status, replace it with delivery_status",
            view_id,
            view_name,
        )
