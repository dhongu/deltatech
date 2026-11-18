from odoo import SUPERUSER_ID, api

ACCESS_NAMES = {
    "access_pricelist_editing": "Permit pricelist editing: Pricelist",
    "access_pricelist_item_editing": "Permit pricelist editing: Pricelist Rule",
}


def migrate(cr, version):
    """The access rights are loaded with noupdate="1", so the readable names given in this
    version do not reach existing databases through the XML data."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    for xmlid, name in ACCESS_NAMES.items():
        access = env.ref(f"deltatech_pricelist_line_viewer.{xmlid}", raise_if_not_found=False)
        if access:
            access.name = name
