# ©  2026 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPartnerGenericLock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.generic_partner = cls.env["res.partner"].create({"name": "Generic"})
        cls.regular_partner = cls.env["res.partner"].create({"name": "Regular customer"})
        cls.env.company.generic_partner_id = cls.generic_partner
        cls.env.company.lock_generic_partner = True

        # Contact creation rights are needed to write on partners at all; they
        # do not grant the right to touch the generic partner.
        base_groups = [
            cls.env.ref("base.group_user").id,
            cls.env.ref("base.group_partner_manager").id,
        ]
        cls.plain_user = cls.env["res.users"].create(
            {
                "name": "Plain user",
                "login": "generic.lock.plain.user",
                # message_post refuses to compute an author without an email
                "email": "generic.lock.plain.user@example.com",
                "groups_id": [(6, 0, base_groups)],
            }
        )
        editor_group = cls.env.ref("deltatech_partner_generic.group_generic_partner_editor")
        cls.editor_user = cls.env["res.users"].create(
            {
                "name": "Editor user",
                "login": "generic.lock.editor.user",
                "email": "generic.lock.editor.user@example.com",
                "groups_id": [(6, 0, base_groups + [editor_group.id])],
            }
        )

    def test_plain_user_cannot_write_generic_partner(self):
        partner = self.generic_partner.with_user(self.plain_user)
        with self.assertRaises(UserError):
            partner.write({"name": "Renamed"})
        self.assertEqual(self.generic_partner.name, "Generic")

    def test_plain_user_cannot_archive_generic_partner(self):
        partner = self.generic_partner.with_user(self.plain_user)
        with self.assertRaises(UserError):
            partner.write({"active": False})
        self.assertTrue(self.generic_partner.active)

    def test_plain_user_cannot_unlink_generic_partner(self):
        partner = self.generic_partner.with_user(self.plain_user)
        with self.assertRaises(UserError):
            partner.unlink()
        self.assertTrue(self.generic_partner.exists())

    def test_plain_user_can_write_regular_partner(self):
        self.regular_partner.with_user(self.plain_user).write({"name": "Renamed"})
        self.assertEqual(self.regular_partner.name, "Renamed")

    def test_editor_user_can_write_generic_partner(self):
        self.generic_partner.with_user(self.editor_user).write({"name": "Renamed"})
        self.assertEqual(self.generic_partner.name, "Renamed")

    def test_chatter_still_works_on_generic_partner(self):
        """Technical writes must not be blocked, otherwise the chatter breaks."""
        partner = self.generic_partner.with_user(self.plain_user)
        partner.message_post(body="A note on the generic partner")
        self.assertTrue(self.generic_partner.message_ids)

    def test_locked_flag_depends_on_the_user(self):
        self.assertTrue(self.generic_partner.with_user(self.plain_user).generic_partner_locked)
        self.assertFalse(self.generic_partner.with_user(self.editor_user).generic_partner_locked)
        self.assertFalse(self.regular_partner.with_user(self.plain_user).generic_partner_locked)

    def test_sudo_is_not_blocked(self):
        """Automated flows running in sudo must keep writing."""
        self.generic_partner.sudo().write({"ref": "SET-BY-AUTOMATION"})
        self.assertEqual(self.generic_partner.ref, "SET-BY-AUTOMATION")

    def test_protection_is_off_by_default(self):
        """Databases that do not ask for the lock keep the old behaviour."""
        self.env.company.lock_generic_partner = False
        self.generic_partner.invalidate_recordset(["generic_partner_locked"])
        partner = self.generic_partner.with_user(self.plain_user)
        self.assertFalse(partner.generic_partner_locked)
        partner.write({"name": "Renamed"})
        self.assertEqual(self.generic_partner.name, "Renamed")

    def test_setting_is_writable_from_the_configuration_screen(self):
        """The related fields must not be readonly, or the settings never save."""
        settings = self.env["res.config.settings"].create(
            {
                "generic_partner_id": self.regular_partner.id,
                "lock_generic_partner": False,
            }
        )
        settings.execute()
        self.assertEqual(self.env.company.generic_partner_id, self.regular_partner)
        self.assertFalse(self.env.company.lock_generic_partner)

    def test_enabling_the_setting_takes_effect_immediately(self):
        """The protected ids are cached: res.company must invalidate them."""
        self.env.company.lock_generic_partner = False
        partner = self.generic_partner.with_user(self.plain_user)
        partner.write({"name": "Allowed while unlocked"})

        self.env.company.lock_generic_partner = True

        with self.assertRaises(UserError):
            partner.write({"name": "Blocked now"})

    def test_disabling_the_setting_takes_effect_immediately(self):
        partner = self.generic_partner.with_user(self.plain_user)
        with self.assertRaises(UserError):
            partner.write({"name": "Blocked"})

        self.env.company.lock_generic_partner = False

        partner.write({"name": "Allowed again"})
        self.assertEqual(self.generic_partner.name, "Allowed again")

    def test_changing_the_generic_partner_takes_effect_immediately(self):
        self.env.company.generic_partner_id = self.regular_partner

        # the former generic partner is free again...
        self.generic_partner.with_user(self.plain_user).write({"name": "Free"})
        # ...and the new one is protected
        with self.assertRaises(UserError):
            self.regular_partner.with_user(self.plain_user).write({"name": "Blocked"})
