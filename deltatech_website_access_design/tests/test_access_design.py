# ©  2015-2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged
from odoo.tools import convert_file

from ..hooks import RESTRICTED_MENUS, post_init_hook, uninstall_hook


@tagged("post_install", "-at_install")
class TestWebsiteAccessDesign(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = cls.env.ref("deltatech_website_access_design.group_user_internal")
        cls.internal_user = cls.env["res.users"].create(
            {
                "name": "TEST Salesman",
                "login": "test_access_design_salesman",
                "group_ids": [(6, 0, [cls.env.ref("base.group_user").id])],
            }
        )
        cls.portal_user = cls.env["res.users"].create(
            {
                "name": "TEST Portal",
                "login": "test_access_design_portal",
                "group_ids": [(6, 0, [cls.env.ref("base.group_portal").id])],
            }
        )

    def _menu_groups(self, xmlid):
        return self.env.ref(xmlid).group_ids

    def test_install_keeps_menus_for_existing_internal_users(self):
        post_init_hook(self.env)
        self.assertIn(self.internal_user, self.group.user_ids)
        self.assertNotIn(self.portal_user, self.group.user_ids)
        for xmlid in RESTRICTED_MENUS:
            self.assertEqual(self._menu_groups(xmlid), self.group, xmlid)

    def test_designer_removed_from_group_loses_menus(self):
        post_init_hook(self.env)
        self.group.write({"user_ids": [(3, self.internal_user.id)]})
        menus = self.env["ir.ui.menu"].with_user(self.internal_user)._visible_menu_ids()
        self.assertNotIn(self.env.ref("contacts.menu_contacts").id, menus)

    def test_uninstall_restores_standard_groups(self):
        post_init_hook(self.env)
        uninstall_hook(self.env)
        self.assertEqual(
            self._menu_groups("contacts.menu_contacts"),
            self.env.ref("base.group_user") | self.env.ref("base.group_partner_manager"),
        )
        for xmlid in ("sale.sale_menu_root", "account.menu_finance_receivables", "account.menu_finance_payables"):
            self.assertFalse(self._menu_groups(xmlid), xmlid)

    def test_update_does_not_touch_menus(self):
        """The data file no longer writes on the standard menus."""
        menu = self.env.ref("contacts.menu_contacts")
        menu.write({"group_ids": [(6, 0, [self.env.ref("base.group_user").id])]})
        convert_file(self.env, "deltatech_website_access_design", "data/data.xml", {}, mode="update", noupdate=False)
        self.assertEqual(menu.group_ids, self.env.ref("base.group_user"))
