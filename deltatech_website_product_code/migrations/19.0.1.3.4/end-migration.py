# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)

VIEW_KEY = "deltatech_website_product_code.product_item_code"


def migrate(cr, version):
    """Pre-migrarea din 19.0.1.0.2 a șters doar view-ul generic `product_item_code`, cu
    arhitectura din 18.0. Copiile per website (COW) au rămas cu xpath-ul pe
    `//div[@itemprop='offers']`, care nu mai există în `website_sale.products_item` din 19.0,
    iar `/shop` pică la randare. View-ul generic a fost recreat, nu rescris, deci loader-ul
    nu a propagat arhitectura nouă spre copii.

    Copiem arhitectura view-ului generic doar în copiile care au încă xpath-ul vechi. Câmpul
    `active` nu e atins, deci opțiunea rămâne activă sau oprită pe fiecare website, așa cum
    a ales clientul în editor."""
    cr.execute(
        SQL(
            """
            UPDATE ir_ui_view cow
               SET arch_db = generic.arch_db
              FROM ir_ui_view generic
             WHERE generic.key = %(key)s
               AND generic.website_id IS NULL
               AND cow.key = %(key)s
               AND cow.website_id IS NOT NULL
               AND cow.arch_db->>'en_US' LIKE %(old_xpath)s
            """,
            key=VIEW_KEY,
            old_xpath="%itemprop='offers'%",
        )
    )
    _logger.info("Reset %s website-specific view(s) %s with the 18.0 arch", cr.rowcount, VIEW_KEY)
