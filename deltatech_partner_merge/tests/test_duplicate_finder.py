# © 2026 Terrabit
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import new_test_user, tagged
from odoo.tests.common import TransactionCase

from odoo.addons.deltatech_partner_match.tools import partner_match as T


@tagged("post_install", "-at_install")
class TestDuplicateFinder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        ro = cls.env.ref("base.ro")
        Partner = cls.env["res.partner"]

        def partner(name, **vals):
            return Partner.create({"name": name, "country_id": ro.id, **vals})

        cls.phone_a = partner("Dupfind Ion Popescu", phone="0722 913 456")
        cls.phone_b = partner("Popescu Ion Dupfind", phone="+40 722 913 456")
        cls.email_a = partner("Dupfind Maria", email="Dupfind.Maria@Example.com ")
        cls.email_b = partner("Dupfind Maria Ionescu", email="dupfind.maria@example.com")
        cls.vat_a = partner("Dupfind Alfa SRL", vat="RO90000910", is_company=True)
        cls.vat_b = partner("Dupfind Alfa S.R.L.", vat="90000910", is_company=True)
        cls.name_a = partner("Gheorghe Dupfindescu", street="Str. Lalelelor nr. 5", city="Cluj-Napoca")
        cls.name_b = partner("Gheorghe Dupfindesc", street="Strada Lalelelor 5", city="Cluj Napoca")
        cls.name_other_street = partner("Gheorghe Dupfindescu", street="Str. Zorilor 12", city="Cluj-Napoca")
        # left out: an internal user and the company itself
        cls.user = new_test_user(cls.env, login="dupfind_internal", groups="base.group_user")
        cls.user.partner_id.write({"phone": "0722 913 456", "country_id": ro.id})
        cls.env.company.partner_id.email = "dupfind.maria@example.com"
        # an invoice address carries the email of its company: not a duplicate
        cls.parent = partner("Dupfind Beta SRL", email="office@dupfind-beta.ro", is_company=True)
        cls.child = partner(
            "Dupfind Beta facturare", email="office@dupfind-beta.ro", type="invoice", parent_id=cls.parent.id
        )
        # the contacts of a company carry its VAT: not duplicates of each other
        cls.vat_contacts = Partner.create(
            [{"name": f"Dupfind Alfa contact {i}", "parent_id": cls.vat_a.id} for i in range(2)]
        )
        # a placeholder phone shared by many partners
        cls.placeholder = Partner
        for i in range(12):
            cls.placeholder |= partner(f"Dupfind Placeholder {i}", phone="0700 000 911")
        cls.env.flush_all()

    def _scan(self, **vals):
        scan = self.env["partner.duplicate.scan"].create({"name": "TEST dupfind", **vals})
        scan.action_scan()
        return scan

    def _group_of(self, scan, partner):
        return scan.group_ids.filtered(lambda g: partner in g.partner_ids)

    # ------------------------------------------------------------------ normalization

    def test_normalize(self):
        self.assertEqual(T.normalize_name("S.C. Popescu Ion S.R.L."), "ion popescu")
        self.assertEqual(T.normalize_name("Ștefănescu  Ana"), T.normalize_name("ana stefanescu"))
        self.assertEqual(T.normalize_vat("RO 123.456"), "123456")
        self.assertEqual(T.normalize_vat("12345678"), "12345678")
        self.assertFalse(T.normalize_vat("RO"))
        self.assertEqual(T.normalize_email(" Ana@Example.COM"), "ana@example.com")
        self.assertEqual(T.normalize_street("Str. Lalelelor nr. 5"), T.normalize_street("Strada Lalelelor 5"))
        self.assertEqual(
            T.phone_key(T.normalize_phone("0722 913 456", "RO")), T.phone_key(T.normalize_phone("+40722913456"))
        )
        self.assertFalse(T.normalize_phone("0000000"))
        if T.phonenumbers:
            self.assertEqual(T.normalize_phone("0722 913 456", "RO"), "+40722913456")

    def test_normalize_without_libraries(self):
        with patch.object(T, "phonenumbers", None), patch.object(T, "unidecode", None):
            self.assertEqual(T.normalize_name("Ștefănescu Ana"), "ana stefanescu")
            self.assertEqual(
                T.phone_key(T.normalize_phone("0722 913 456")), T.phone_key(T.normalize_phone("+40 722 913 456"))
            )

    # ------------------------------------------------------------------ groups

    def test_exact_keys(self):
        scan = self._scan(use_name=False)
        phone = self._group_of(scan, self.phone_a)
        self.assertEqual(phone.partner_ids, self.phone_a | self.phone_b)
        self.assertEqual(phone.match_type, "exact")
        self.assertIn("same phone", phone.reasons)
        self.assertEqual(self._group_of(scan, self.email_a).partner_ids, self.email_a | self.email_b)
        vat = self._group_of(scan, self.vat_a)
        self.assertEqual(vat.partner_ids, self.vat_a | self.vat_b)
        self.assertEqual(vat.score, 100)
        self.assertFalse(self._group_of(scan, self.vat_contacts[0]), "contacts inherit the VAT of their company")

    def test_exclusions(self):
        scan = self._scan()
        found = scan.group_ids.partner_ids
        self.assertNotIn(self.user.partner_id, found)
        self.assertNotIn(self.env.company.partner_id, found)
        self.assertFalse(self._group_of(scan, self.child), "an address of the same customer is not a duplicate")
        self.assertFalse(found & self.placeholder, "a value shared by too many partners is skipped")
        self.assertIn("0700000911"[-9:], scan.report)

    def _check_fuzzy(self, scan):
        group = self._group_of(scan, self.name_a)
        self.assertEqual(group.partner_ids, self.name_a | self.name_b)
        self.assertEqual(group.match_type, "fuzzy")
        self.assertIn("same street", group.reasons)
        self.assertGreaterEqual(group.score, 90)

    def test_fuzzy_names(self):
        self._check_fuzzy(self._scan(use_vat=False, use_phone=False, use_email=False))

    def test_fuzzy_names_fallback(self):
        with patch.object(T, "rf_process", None):
            scan = self._scan(use_vat=False, use_phone=False, use_email=False)
        self.assertEqual(scan.engine, "difflib")
        self._check_fuzzy(scan)

    def test_fuzzy_name_only(self):
        scan = self._scan(use_vat=False, use_phone=False, use_email=False, name_match="name")
        self.assertIn(self.name_other_street, self._group_of(scan, self.name_a).partner_ids)

    def test_block_by_prefix(self):
        scan = self._scan(use_vat=False, use_phone=False, use_email=False, block_by="prefix")
        self._check_fuzzy(scan)

    # ------------------------------------------------------------------ review

    def test_ignore_survives_rescan(self):
        scan = self._scan(use_name=False)
        group = self._group_of(scan, self.phone_a)
        group.action_ignore()
        self.assertEqual(group.state, "ignored")
        scan.action_scan()
        self.assertFalse(self._group_of(scan, self.phone_a))
        self.assertTrue(self._group_of(scan, self.email_a), "other groups are still found")

    def test_reopen_forgets_ignored_pairs(self):
        scan = self._scan(use_name=False)
        group = self._group_of(scan, self.phone_a)
        group.action_ignore()
        group.action_reopen()
        self.assertEqual(group.state, "new")
        self.assertFalse(self.env["partner.duplicate.ignore"].search([("partner_a_id", "=", self.phone_a.id)]))

    def test_merge_with_standard_wizard(self):
        scan = self._scan(use_name=False)
        group = self._group_of(scan, self.phone_a)
        action = group.action_merge()
        self.assertEqual(action["res_model"], "base.partner.merge.automatic.wizard")
        self.assertEqual(sorted(action["context"]["active_ids"]), sorted((self.phone_a | self.phone_b).ids))
        wizard = self.env[action["res_model"]].with_context(**action["context"]).create({})
        self.assertEqual(wizard.partner_ids, self.phone_a | self.phone_b)
        wizard.action_merge()
        scan.action_refresh()
        self.assertEqual(group.state, "merged")
        self.assertEqual(group.partner_count, 1)
        self.assertEqual(group.action_merge()["tag"], "display_notification")

    def test_merge_wizard_limit(self):
        extra = self.env["res.partner"].create(
            [{"name": f"Dupfind Quad {i}", "email": "dupfind.quad@example.com"} for i in range(4)]
        )
        scan = self._scan(use_name=False, use_phone=False, use_vat=False)
        group = self._group_of(scan, extra[0])
        self.assertEqual(group.partner_ids, extra)
        self.assertEqual(len(group.action_merge()["context"]["active_ids"]), 3)
