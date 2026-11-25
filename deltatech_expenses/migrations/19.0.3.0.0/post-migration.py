# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Mapează partenerii vechi (x_old_partner_id) la `hr.employee` prin
    `work_contact_id`; creează angajatul dacă nu există. Populează apoi
    `employee_id` (hr.employee) și `partner_id` (related stored)."""
    if not version:
        return

    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'deltatech_expenses_deduction'
          AND column_name = 'x_old_partner_id'
        """
    )
    if not cr.fetchone():
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    Employee = env["hr.employee"].with_context(active_test=False)

    # maparea se face pe (companie, partener): un contact comun mai multor companii are câte un
    # angajat în fiecare, iar deducerea trebuie legată de angajatul din compania ei
    cr.execute(
        """
        SELECT DISTINCT company_id, x_old_partner_id
        FROM deltatech_expenses_deduction
        WHERE x_old_partner_id IS NOT NULL
        """
    )
    pairs = cr.fetchall()

    for company_id, partner_id in pairs:
        partner = env["res.partner"].browse(partner_id).exists()
        if not partner:
            continue
        company = env["res.company"].browse(company_id).exists() or env.company
        employee = Employee.search(
            [("work_contact_id", "=", partner.id), ("company_id", "=", company.id)],
            order="active desc, id",
            limit=1,
        )
        if not employee:
            employee = Employee.with_company(company).create(
                {
                    "name": partner.name or "Angajat",
                    "work_contact_id": partner.id,
                    "company_id": company.id,
                }
            )
            _logger.info(
                "deltatech_expenses: creat hr.employee %s în compania %s pentru partenerul %s",
                employee.id,
                company.id,
                partner.id,
            )

        cr.execute(
            """
            UPDATE deltatech_expenses_deduction
            SET employee_id = %s
            WHERE x_old_partner_id = %s
              AND company_id IS NOT DISTINCT FROM %s
            """,
            (employee.id, partner.id, company_id),
        )

    # partner_id este related stored la employee_id.work_contact_id, deci
    # egal cu partenerul original — îl setăm direct pentru rândurile migrate
    cr.execute(
        """
        UPDATE deltatech_expenses_deduction
        SET partner_id = x_old_partner_id
        WHERE x_old_partner_id IS NOT NULL
        """
    )

    # curățăm coloana temporară
    cr.execute("ALTER TABLE deltatech_expenses_deduction DROP COLUMN x_old_partner_id")
    _logger.info("deltatech_expenses: migrare res.partner -> hr.employee finalizată")
