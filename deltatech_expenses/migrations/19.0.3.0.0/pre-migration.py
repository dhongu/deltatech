# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Înainte ca `employee_id` să devină Many2one către `hr.employee`, salvăm
    valorile vechi (id-uri `res.partner`) într-o coloană temporară, ca să nu fie
    interpretate greșit drept id-uri de angajat."""
    if not version:
        return

    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'deltatech_expenses_deduction'
          AND column_name = 'employee_id'
        """
    )
    if not cr.fetchone():
        return

    # redenumim coloana existentă (id-uri res.partner) -> x_old_partner_id
    cr.execute(
        """
        ALTER TABLE deltatech_expenses_deduction
        RENAME COLUMN employee_id TO x_old_partner_id
        """
    )
    # eliminăm eventualul NOT NULL moștenit, ca recrearea coloanei employee_id
    # (acum hr.employee) să nu fie blocată pe rândurile existente
    cr.execute(
        """
        ALTER TABLE deltatech_expenses_deduction
        ALTER COLUMN x_old_partner_id DROP NOT NULL
        """
    )
    _logger.info("deltatech_expenses: employee_id (res.partner) salvat temporar în x_old_partner_id")
