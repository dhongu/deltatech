# ©  2008-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Restore the standard vehicle category emptied by the pre-migration and
    give the map sheet sequence its code: it was loaded without one
    (noupdate data), so next_by_code("fleet.map.sheet") never found it."""
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    vehicles = (
        env["fleet.vehicle"]
        .with_context(active_test=False)
        .search([("category_id", "=", False), ("model_id.category_id", "!=", False)])
    )
    for vehicle in vehicles:
        vehicle.category_id = vehicle.model_id.category_id
    sequence = env.ref("deltatech_fleet.sequence_fleet_road_map", raise_if_not_found=False)
    if sequence and not sequence.code:
        sequence.code = "fleet.map.sheet"
