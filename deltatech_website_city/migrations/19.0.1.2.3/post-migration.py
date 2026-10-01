# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Fill the free-text city of the partners created at checkout since 19.0.

    The checkout saved only ``city_id``, which left ``city`` empty and blocked
    posting their invoices.
    """
    env = api.Environment(cr, SUPERUSER_ID, {"active_test": False})
    partners = env["res.partner"].search([("city_id", "!=", False), ("city", "in", [False, ""])])
    for city in partners.city_id:
        partners.filtered(lambda partner, city=city: partner.city_id == city).write({"city": city.name})
