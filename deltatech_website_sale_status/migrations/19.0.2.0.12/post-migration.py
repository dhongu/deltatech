# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Restore the stage the 19.0.2.0.11 post-migration changed.

    The detailed stage (`placed`, carrier status) is now an option, off by
    default: the website quotations sent and the orders left on a carrier
    status get back the stage of the stock moves (`delivered` at the
    validation of the transfers). The orders the old migration made
    `delivered` after the carrier keep it: their transfers are validated.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {"tracking_disable": True})
    SaleOrder = env["sale.order"]
    orders = SaleOrder.search([("stage", "=", "placed")])
    orders |= SaleOrder.search([("state", "=", "sale"), ("stage", "in", ["pre_advice", "in_delivery"])])
    env.add_to_compute(SaleOrder._fields["stage"], orders)
    orders.flush_recordset(["stage"])
