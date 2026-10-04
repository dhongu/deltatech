# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """Recompute the stage of the orders the fixed computation changes.

    The stage is stored: the website quotations sent to the customer (now
    `placed`) and the orders whose transfers have a carrier status (now
    `pre_advice`/`in_delivery`/`delivered` after the parcel) would keep the
    value of the old computation until their next change.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {"tracking_disable": True})
    SaleOrder = env["sale.order"]
    orders = SaleOrder.search([("state", "=", "sent"), ("website_id", "!=", False)])
    orders |= SaleOrder.search(
        [
            ("state", "=", "sale"),
            ("picking_ids.delivery_state", "in", ["pre_advice", "in_transit", "in_warehouse", "in_delivery"]),
        ]
    )
    orders |= SaleOrder.search(
        [
            ("state", "=", "sale"),
            ("stage", "!=", "delivered"),
            ("picking_ids.delivery_state", "=", "delivered"),
        ]
    )
    env.add_to_compute(SaleOrder._fields["stage"], orders)
    orders.flush_recordset(["stage"])
