# © 2026 Deltatech / Terrabit
from odoo.exceptions import AccessError
from odoo.tests import new_test_user
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestNormalizeAccess(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = new_test_user(
            cls.env, login="dt_normalize_internal", groups="base.group_user,base.group_partner_manager"
        )
        cls.admin = new_test_user(cls.env, login="dt_normalize_admin", groups="base.group_user,base.group_system")
        cls.company = cls.env["res.partner"].create({"name": "Norm Delta srl", "vat": "RO14399840"})
        cls.contact = cls.env["res.partner"].create({"name": "Ion", "parent_id": cls.company.id})

    def test_internal_user_cannot_normalize(self):
        Partner = self.env["res.partner"].with_user(self.user)
        with self.assertRaises(AccessError):
            Partner.batch_normalize_company_names()
        with self.assertRaises(AccessError):
            Partner.cron_normalize_company_names()
        self.company.invalidate_recordset()
        self.assertEqual(self.company.name, "Norm Delta srl")

    def test_admin_normalizes_and_names_are_refreshed(self):
        self.env["res.partner"].with_user(self.admin).batch_normalize_company_names()
        self.assertEqual(self.company.name, "Norm Delta S.R.L.")
        self.assertEqual(self.company.complete_name, "Norm Delta S.R.L.")
        self.assertEqual(self.contact.complete_name, "Norm Delta S.R.L., Ion")
