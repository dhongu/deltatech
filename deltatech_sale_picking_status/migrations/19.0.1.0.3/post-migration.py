# See README.rst file on addons root folder for license details

from odoo import SUPERUSER_ID, api

BATCH_SIZE = 1000


def migrate(cr, version):
    """picking_status became a stored computed field: recompute the values
    left wrong by the previous version (e.g. orders reset to quotation)."""
    if not version:
        return
    # fara mesaje de tracking in chatter pentru recalcularea in masa
    env = api.Environment(cr, SUPERUSER_ID, {"tracking_disable": True})
    SaleOrder = env["sale.order"]
    field = SaleOrder._fields["picking_status"]
    order_ids = SaleOrder.search([]).ids
    for start in range(0, len(order_ids), BATCH_SIZE):
        orders = SaleOrder.browse(order_ids[start : start + BATCH_SIZE])
        env.add_to_compute(field, orders)
        orders.flush_recordset(["picking_status"])
        env.invalidate_all()
