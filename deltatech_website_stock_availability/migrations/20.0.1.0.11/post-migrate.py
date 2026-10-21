# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo import SUPERUSER_ID, api

OLD_VIEW_KEY = "deltatech_website_stock_availability.products_qty_available"
STOCK_CLASSES = "o_wsale_products_opt_stock_text"


def migrate(cr, version):
    """The shop card badge is no longer a customize view: it is configured from the
    website builder. Keep it visible, as text above the price, where it was active."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    views = env["ir.ui.view"].with_context(active_test=False).search([("key", "=", OLD_VIEW_KEY)])
    if not views:
        return
    generic = views.filtered(lambda v: not v.website_id)
    for website in env["website"].search([]):
        view = views.filtered(lambda v, w=website: v.website_id == w) or generic
        if not view or not view[0].active:
            continue
        classes = (website.shop_opt_products_design_classes or "").split()
        if STOCK_CLASSES not in classes:
            website.shop_opt_products_design_classes = " ".join(classes + [STOCK_CLASSES])
    # the generic view is removed with its xml id; website copies have none
    views.filtered("website_id").unlink()
