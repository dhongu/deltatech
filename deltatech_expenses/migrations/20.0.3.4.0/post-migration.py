# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo.tools import SQL

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Până la această versiune, suma unei linii cu taxă „pe deasupra" (taxele RO standard de
    achiziție) era tratată ca bază, iar TVA-ul se adăuga peste ea. Acum suma este mereu brută (cea
    de pe bon). Ca liniile existente să-și păstreze baza și TVA-ul, suma lor devine brutul calculat
    anterior (bază + TVA). Liniile cu taxă inclusă în preț au deja suma brută (amount != bază)."""
    if not version:
        return
    cr.execute(
        SQL(
            """
            UPDATE deltatech_expenses_deduction_line
               SET amount = price_subtotal + tax_amount
             WHERE tax_amount != 0
               AND amount = price_subtotal
            """
        )
    )
    _logger.info("deltatech_expenses: %s linii de decont trecute pe suma cu TVA inclus", cr.rowcount)
