# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)

OLD_VIEW_KEY = "deltatech_website_stock_availability.products_qty_available"
KEPT_VIEW_KEY = "deltatech_website_stock_availability.products_qty_available_custom"
STOCK_CLASSES = "o_wsale_products_opt_stock_text"


def migrate(cr, version):
    """The shop card badge is no longer a customize view: it is configured from the
    website builder. Keep it visible, as text above the price, where it was active."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    views = env["ir.ui.view"].with_context(active_test=False).search([("key", "=", OLD_VIEW_KEY)])
    if not views:
        return
    generic = views.filtered(lambda v: not v.website_id)
    # A website copy inherited by other views (customizations made on the database) is
    # kept, under a key of its own: with the old key it would be removed together with
    # the generic view, and its children with it. That website keeps its own rendering.
    kept = views.filtered(lambda v: v.website_id and v.inherit_children_ids)
    for website in env["website"].search([]):
        view = views.filtered(lambda v, w=website: v.website_id == w) or generic
        if not view or not view[0].active or view & kept:
            continue
        classes = (website.shop_opt_products_design_classes or "").split()
        if STOCK_CLASSES not in classes:
            website.shop_opt_products_design_classes = " ".join(classes + [STOCK_CLASSES])
    for view in kept:
        _logger.warning(
            "View %s (website %s) is inherited by %s: kept as %s, the stock status of the shop card is not enabled",
            view.id,
            view.website_id.name,
            ", ".join(view.inherit_children_ids.mapped("key")),
            KEPT_VIEW_KEY,
        )
    kept.write({"key": KEPT_VIEW_KEY})
    # the generic view is removed with its xml id; website copies have none
    (views.filtered("website_id") - kept).unlink()
