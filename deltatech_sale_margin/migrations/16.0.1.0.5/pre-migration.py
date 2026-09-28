from odoo import SUPERUSER_ID, api


def unlink_view(env, xml_id):
    view = env.ref(xml_id, raise_if_not_found=False)
    if view and view.exists():
        view.unlink()


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    unlink_view(env, "deltatech_sale_margin.sale_margin_sale_order")
