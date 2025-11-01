# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestResPartnerActions(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create some partners/companies for tests
        cls.company1 = cls.env["res.partner"].create(
            {
                "name": "ACME srl",
                "is_company": True,
            }
        )
        cls.company2 = cls.env["res.partner"].create(
            {
                "name": "Beta s.a",
                "is_company": True,
            }
        )

        cls.contact_a1 = cls.env["res.partner"].create(
            {
                "name": "John Doe",
                "email": "john@example.com",
                "is_company": False,
            }
        )
        cls.contact_a2 = cls.env["res.partner"].create(
            {
                "name": "John X",
                "email": "john@example.com",
                "is_company": False,
            }
        )

        cls.comp_dup1 = cls.env["res.partner"].create(
            {
                "name": "Umbrella SRL",
                "is_company": True,
                "vat": "RO123456789",
                "active": True,
            }
        )
        cls.comp_dup2 = cls.env["res.partner"].create(
            {
                "name": "Umbrella SRL 2",
                "is_company": True,
                "vat": "RO123456789",
                "active": True,
            }
        )

    def test_batch_normalize_company_names(self):
        # Sanity preconditions
        self.assertIn("srl", self.company1.name.lower())
        self.assertIn("s.a", self.company2.name.lower())

        updated = self.env["res.partner"].batch_normalize_company_names(batch_size=100)
        # Should update at least our two companies
        self.assertGreaterEqual(updated, 2)

        self.company1.invalidate_recordset()
        self.company2.invalidate_recordset()
        self.assertEqual(self.company1.name, "ACME S.R.L.")
        self.assertEqual(self.company2.name, "Beta S.A.")

    def test_cron_normalize_company_names(self):
        # Create an extra company that needs normalization
        company3 = self.env["res.partner"].create(
            {
                "name": "Gamma pfa",
                "is_company": True,
            }
        )
        # Should not raise; it logs and may post messages to admins
        self.env["res.partner"].cron_normalize_company_names()
        company3.invalidate_recordset()
        self.assertEqual(company3.name, "Gamma P.F.A.")

    def test_compute_vies_valid_skip_context(self):
        # Ensure the context skip path does not raise and returns None
        partner = self.env["res.partner"].create(
            {
                "name": "VIES Test",
                "vat": "RO20603502",
                "is_company": True,
            }
        )
        # Call with skip flag; just ensure no exception
        partner.with_context(skip_vies_check=True)._compute_vies_valid()

    def test_cron_merge_duplicate_contacts_conditional(self):
        # If merge wizard isn't installed/available, skip this test gracefully
        try:
            _ = self.env["base.partner.merge.automatic.wizard"]
        except KeyError:
            self.skipTest("base_partner_merge wizard not available; skipping duplicate contacts merge test")

        # Run the cron and assert duplicates reduced
        # Limit high enough to include our duplicates
        self.env["res.partner"]._cron_merge_duplicate_contacts(limit=20)

        # Re-fetch by email to verify only one remains
        contacts = self.env["res.partner"].search(
            [
                ("email", "=", "john@example.com"),
                ("is_company", "=", False),
                ("vat", "=", False),
            ]
        )
        self.assertLessEqual(len(contacts), 1)

    def test_cron_merge_duplicate_companies_conditional(self):
        try:
            _ = self.env["base.partner.merge.automatic.wizard"]
        except KeyError:
            self.skipTest("base_partner_merge wizard not available; skipping duplicate companies merge test")

        self.env["res.partner"]._cron_merge_duplicate_companies(limit=20)

        companies = self.env["res.partner"].search(
            [
                ("vat", "=", "RO12345678"),
                ("is_company", "=", True),
                ("parent_id", "=", False),
                ("active", "=", True),
            ]
        )
        self.assertLessEqual(len(companies), 1)
