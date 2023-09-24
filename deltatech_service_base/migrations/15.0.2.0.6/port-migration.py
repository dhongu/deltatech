# ©  2008-2021 Deltatech
# See README.rst file on addons root folder for license details

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    # e instala modulul date.range ?
    if env["ir.module.module"].search([("name", "=", "date_range"), ("state", "=", "installed")]):
        ranges = env["date.range"].search([])
        for date_range in ranges:
            name = date_range.name
            if not env["service.date.range"].search([("name", "=", name)]):
                env["service.date.range"].create(
                    {
                        "name": name,
                        "date_start": date_range.date_start,
                        "date_end": date_range.date_end,
                    }
                )
