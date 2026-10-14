from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    """The groups are loaded with noupdate="1", so the privilege added in this
    version does not reach existing databases through the XML data."""
    env = api.Environment(cr, SUPERUSER_ID, {})
    privilege = env.ref("deltatech_agreement_management.privilege_agreement", raise_if_not_found=False)
    if not privilege:
        return
    for xmlid in ("group_agreement_user", "group_agreement_manager"):
        group = env.ref(f"deltatech_agreement_management.{xmlid}", raise_if_not_found=False)
        if group and not group.privilege_id:
            group.privilege_id = privilege
