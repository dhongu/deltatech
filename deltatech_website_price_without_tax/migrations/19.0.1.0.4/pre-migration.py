# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)

VIEW_KEY = "deltatech_website_price_without_tax.product_price_without_tax"


def migrate(cr, version):
    """Pe bazele venite din 18.0, view-ul generic are încă arhitectura veche, cu xpath pe
    `//div[@itemprop='offers']`, care nu mai există în `website_sale.product_price` din 19.0.
    Dacă există și o copie per website (COW), loader-ul o scrie înaintea view-ului generic,
    iar validarea ei combină view-ul generic vechi și eșuează.

    Dezactivăm temporar doar view-ul generic vechi și îi reținem id-ul; end-migration îl
    reactivează. Copiile per website nu sunt atinse, deci starea aleasă de client în editor
    (opțiunea activă sau oprită pe fiecare website) rămâne neschimbată."""
    if not version:
        return

    cr.execute(
        SQL(
            """
            CREATE TABLE IF NOT EXISTS deltatech_pwt_reactivate (view_id integer);
            WITH deactivated AS (
                UPDATE ir_ui_view SET active = false
                WHERE key = %s
                  AND website_id IS NULL
                  AND active
                  AND arch_db->>'en_US' LIKE %s
                RETURNING id
            )
            INSERT INTO deltatech_pwt_reactivate SELECT id FROM deactivated
            """,
            VIEW_KEY,
            "%itemprop='offers'%",
        )
    )
    _logger.info("Deactivated %s view(s) %s with the 18.0 arch", cr.rowcount, VIEW_KEY)
