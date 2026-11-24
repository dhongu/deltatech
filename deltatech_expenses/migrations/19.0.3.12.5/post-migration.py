# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Repară deducerile legate de angajatul altei companii de migrarea 19.0.3.0.0 (EXPENSES-003).

    Migrarea veche mapa partenerul la primul angajat găsit după `work_contact_id`, fără companie,
    așa că deducerile unui contact comun mai multor companii primeau toate angajatul unei singure
    companii. `partner_id` a păstrat partenerul original, deci deducerea se leagă acum de angajatul
    cu același contact din compania ei. Unde un astfel de angajat nu există, nu creăm unul (deducerea
    poate fi o alegere voită, ulterioară migrării): o raportăm în log, pentru corectare manuală."""
    if not version:
        return

    cr.execute(
        """
        SELECT d.company_id, d.partner_id, array_agg(d.id ORDER BY d.id)
        FROM deltatech_expenses_deduction d
        JOIN hr_employee e ON e.id = d.employee_id
        WHERE e.company_id <> d.company_id
          AND d.partner_id IS NOT NULL
        GROUP BY d.company_id, d.partner_id
        """
    )
    groups = cr.fetchall()
    if not groups:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    Employee = env["hr.employee"].with_context(active_test=False)
    for company_id, partner_id, deduction_ids in groups:
        employee = Employee.search(
            [("work_contact_id", "=", partner_id), ("company_id", "=", company_id)],
            order="active desc, id",
            limit=1,
        )
        if not employee:
            _logger.warning(
                "deltatech_expenses: deducerile %s (compania %s) au angajatul altei companii și nu există "
                "un angajat cu contactul %s în compania lor; corectați manual angajatul",
                deduction_ids,
                company_id,
                partner_id,
            )
            continue
        cr.execute(
            "UPDATE deltatech_expenses_deduction SET employee_id = %s WHERE id = ANY(%s)",
            (employee.id, deduction_ids),
        )
        _logger.info(
            "deltatech_expenses: deducerile %s (compania %s) mutate pe angajatul %s",
            deduction_ids,
            company_id,
            employee.id,
        )
