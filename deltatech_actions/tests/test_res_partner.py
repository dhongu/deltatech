# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests.common import TransactionCase, tagged

from ..models.res_partner import DUPLICATE_COMPANIES_SQL, DUPLICATE_CONTACTS_SQL


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

    def _create_contact_duplicates(self, email, count=2):
        return self.env["res.partner"].create(
            [{"name": f"Dup {email} {i}", "email": email, "is_company": False} for i in range(count)]
        )

    def _manual_progress(self, xmlid):
        """Context of a "Run manually": progress without cron_id."""
        cron = self.env.ref(xmlid)
        cron.active = True  # Odoo ignores triggers on inactive crons
        cron, progress = cron._add_progress()
        return cron, progress

    def _triggers(self, cron):
        return self.env["ir.cron.trigger"].search([("cron_id", "=", cron.id)])

    def test_cron_merge_duplicate_contacts_progress(self):
        self._create_contact_duplicates("dup1@example.com")
        self._create_contact_duplicates("dup2@example.com")
        cron, progress = self._manual_progress("deltatech_actions.ir_cron_merge_contacts")
        total = self.env["res.partner"]._count_duplicate_groups(DUPLICATE_CONTACTS_SQL)
        self.assertGreaterEqual(total, 3)

        self.env["res.partner"].with_context(ir_cron_progress_id=progress.id)._cron_merge_duplicate_contacts(limit=1)

        self.assertEqual(progress.done, 1)
        self.assertEqual(progress.remaining, total - 1)
        # manual run: the rest is processed in the background
        self.assertEqual(len(self._triggers(cron)), 1)

    def test_cron_merge_duplicate_contacts_scheduler_no_trigger(self):
        cron, progress = self._manual_progress("deltatech_actions.ir_cron_merge_contacts")
        self._create_contact_duplicates("dup3@example.com")
        self.env["res.partner"].with_context(
            ir_cron_progress_id=progress.id, cron_id=cron.id
        )._cron_merge_duplicate_contacts(limit=1)
        self.assertEqual(progress.done, 1)
        self.assertGreater(progress.remaining, 0)
        # scheduler run: the native loop takes care of the rest
        self.assertFalse(self._triggers(cron))

    def test_cron_merge_duplicate_contacts_failed_group(self):
        """A failed merge is rolled back alone; the other groups of the batch are merged."""
        self._create_contact_duplicates("dup4@example.com")
        cron, progress = self._manual_progress("deltatech_actions.ir_cron_merge_contacts")
        Wizard = type(self.env["base.partner.merge.automatic.wizard"])
        original_merge = Wizard.action_merge
        calls = []

        def action_merge(wizard):
            calls.append(wizard.partner_ids.mapped("email"))
            if len(calls) == 1:
                raise RuntimeError("merge failed")
            return original_merge(wizard)

        with patch.object(Wizard, "action_merge", action_merge):
            self.env["res.partner"].with_context(ir_cron_progress_id=progress.id)._cron_merge_duplicate_contacts(
                limit=20
            )

        failed_email = calls[0][0]
        self.assertEqual(len(self.env["res.partner"].search([("email", "=", failed_email)])), 2)
        self.assertEqual(progress.done, len(calls) - 1)
        self.assertEqual(progress.remaining, 1)

    def test_cron_merge_duplicate_contacts_all_failed_stops(self):
        self._create_contact_duplicates("dup5@example.com")
        cron, progress = self._manual_progress("deltatech_actions.ir_cron_merge_contacts")
        Wizard = type(self.env["base.partner.merge.automatic.wizard"])

        def action_merge(wizard):
            raise RuntimeError("merge failed")

        with patch.object(Wizard, "action_merge", action_merge):
            self.env["res.partner"].with_context(ir_cron_progress_id=progress.id)._cron_merge_duplicate_contacts(
                limit=20
            )

        # no progress: remaining forced to 0 and no retrigger
        self.assertEqual((progress.done, progress.remaining), (0, 0))
        self.assertFalse(self._triggers(cron))

    def test_cron_merge_duplicate_companies_progress(self):
        self.env["res.partner"].create(
            [{"name": f"Dup Co {i}", "is_company": True, "vat": "RO99999999"} for i in range(2)]
        )
        cron, progress = self._manual_progress("deltatech_actions.ir_cron_merge_companies")
        total = self.env["res.partner"]._count_duplicate_groups(DUPLICATE_COMPANIES_SQL)
        self.assertGreaterEqual(total, 2)

        self.env["res.partner"].with_context(ir_cron_progress_id=progress.id)._cron_merge_duplicate_companies(limit=1)

        self.assertEqual(progress.done, 1)
        self.assertEqual(progress.remaining, total - 1)
        self.assertEqual(len(self._triggers(cron)), 1)

    def test_normalize_company_names_idempotent(self):
        already = self.env["res.partner"].create({"name": "Delta S.R.L.", "is_company": True})
        self.env["res.partner"].batch_normalize_company_names(batch_size=1000)
        self.assertEqual(self.env["res.partner"]._count_companies_to_normalize(), 0)
        # names already normalized are not selected again
        self.assertEqual(self.env["res.partner"].batch_normalize_company_names(batch_size=1000), 0)
        self.assertEqual(already.name, "Delta S.R.L.")

    def test_normalize_company_names_updates_complete_name(self):
        self.env["res.partner"].batch_normalize_company_names(batch_size=1000)
        self.assertEqual(self.company1.complete_name, "ACME S.R.L.")

    def test_cron_normalize_company_names_progress(self):
        self.env["res.partner"].create([{"name": f"Batch {i} srl", "is_company": True} for i in range(3)])
        cron, progress = self._manual_progress("deltatech_actions.cron_normalize_company_names")
        total = self.env["res.partner"]._count_companies_to_normalize()
        Partner = self.env["res.partner"].with_context(ir_cron_progress_id=progress.id)
        admin_partner = self.env.ref("base.user_admin").partner_id

        Partner.cron_normalize_company_names(batch_size=2)
        self.assertEqual((progress.done, progress.remaining), (2, total - 2))
        self.assertEqual(len(self._triggers(cron)), 1)
        # admins are notified only at the end
        subject = "Normalizare companii - Cron Job"
        self.assertFalse(admin_partner.message_ids.filtered(lambda m: m.subject == subject))

        Partner.cron_normalize_company_names(batch_size=1000)
        self.assertEqual(progress.remaining, 0)
        self.assertTrue(admin_partner.message_ids.filtered(lambda m: m.subject == subject))
