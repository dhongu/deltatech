# ©  2015-2026 Deltatech
# See README.rst file on addons root folder for license details

# Menus reserved to the group "Access Partners, Sale, Invoice", with the
# groups their own module gives them on Odoo 19 (restored at uninstall).
RESTRICTED_MENUS = {
    "contacts.menu_contacts": ["base.group_user", "base.group_partner_manager"],
    "sale.sale_menu_root": [],
    "account.menu_finance_receivables": [],
    "account.menu_finance_payables": [],
}

ACCESS_GROUP = "deltatech_website_access_design.group_user_internal"


def post_init_hook(env):
    """Restrict the menus once, at installation, without hiding them from anyone.

    Every internal user existing at installation joins the access group, so
    nobody loses the menus; the administrator then removes the web designer.
    Runs only at installation, not at module update.
    """
    group = env.ref(ACCESS_GROUP)
    users = env["res.users"].with_context(active_test=False).search([("share", "=", False)])
    group.write({"user_ids": [(4, user.id) for user in users]})
    for xmlid in RESTRICTED_MENUS:
        menu = env.ref(xmlid, raise_if_not_found=False)
        if menu:
            menu.write({"group_ids": [(6, 0, group.ids)]})


def uninstall_hook(env):
    """Give the menus back the groups set by their own module."""
    for xmlid, group_xmlids in RESTRICTED_MENUS.items():
        menu = env.ref(xmlid, raise_if_not_found=False)
        if not menu:
            continue
        groups = [env.ref(g, raise_if_not_found=False) for g in group_xmlids]
        menu.write({"group_ids": [(6, 0, [g.id for g in groups if g])]})
