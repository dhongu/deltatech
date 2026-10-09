# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)

VIEW_KEY = "deltatech_website_city.address"


def migrate(cr, version):
    """In 18.0 the city field was added by the view `address`, inheriting `website_sale.address`.
    In 19.0 the address form moved to `portal.address_form_fields` and the view was renamed
    `address_form_fields`. The old view stayed in the database, orphaned and still pointing at
    `<div id="div_city">`, which `website_sale.address` no longer contains, so every website
    reported it as a broken template. The old view is removed, together with its external id;
    the new view is loaded from the module data."""
    cr.execute(
        SQL(
            """
            DELETE FROM ir_ui_view
             WHERE key = %(key)s
            """,
            key=VIEW_KEY,
        )
    )
    _logger.info("Deleted %s orphan view(s) %s", cr.rowcount, VIEW_KEY)
    cr.execute(
        SQL(
            """
            DELETE FROM ir_model_data
             WHERE module = 'deltatech_website_city'
               AND name = 'address'
               AND model = 'ir.ui.view'
            """
        )
    )
