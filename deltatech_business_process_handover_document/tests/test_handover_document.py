# © 2025 Deltatech
# See README.rst file on addons root folder for license details

from odoo import fields as odoo_fields
from odoo.tests.common import TransactionCase


class TestHandoverDocument(TransactionCase):
    def setUp(self):
        super().setUp()
        # Minimal partner to use for M2O/M2M fields
        self.partner = self.env["res.partner"].search([], limit=1)
        if not self.partner:
            self.partner = self.env["res.partner"].create({"name": "Test Partner"})

        # Minimal business project
        self.project = self.env["business.project"].create(
            {
                "name": "Test Project",
                "customer_id": self.partner.id,
            }
        )
        self.area = self.env["business.area"].create(
            {
                "name": "ERP",
            }
        )

    def test_extended_fields_exist_and_types(self):
        Project = self.env["business.project"]
        f = Project._fields

        # Char fields
        self.assertIn("provider_company", f)
        self.assertIsInstance(f["provider_company"], odoo_fields.Char)

        self.assertIn("recipient_company", f)
        self.assertIsInstance(f["recipient_company"], odoo_fields.Char)

        # Many2one fields with domain to non-company partners
        self.assertIn("provider_representative", f)
        self.assertIsInstance(f["provider_representative"], odoo_fields.Many2one)
        # Domain may be stored as string or list; check semantic key
        self.assertIn("is_company", str(f["provider_representative"].domain))

        self.assertIn("recipient_representative", f)
        self.assertIsInstance(f["recipient_representative"], odoo_fields.Many2one)
        self.assertIn("is_company", str(f["recipient_representative"].domain))

        # Many2many tester fields to partners
        self.assertIn("provider_testers", f)
        self.assertIsInstance(f["provider_testers"], odoo_fields.Many2many)

        self.assertIn("recipient_testers", f)
        self.assertIsInstance(f["recipient_testers"], odoo_fields.Many2many)

        # One2many computed field to developments
        self.assertIn("development_ids", f)
        self.assertIsInstance(f["development_ids"], odoo_fields.One2many)

    def test_compute_development_ids_links_records(self):
        # Initially, no developments should be linked
        self.project._compute_development_ids()
        self.assertFalse(self.project.development_ids, "Expected no developments initially")

        # Create development linked to this project
        dev_type = self.env["business.development.type"].create({"name": "Backend"})
        dev = self.env["business.development"].create(
            {
                "name": "Add feature X",
                "type_id": dev_type.id,
                "project_id": self.project.id,
                "area_id": self.area.id,
            }
        )

        # Recompute and assert linkage
        self.project._compute_development_ids()
        self.assertIn(dev, self.project.development_ids)

    def test_report_action_available(self):
        # Ensure the report action defined by this module exists and can be retrieved
        action = self.env.ref("deltatech_business_process_handover_document.action_report_verbal_process")
        self.assertEqual(action.model, "business.project")
        # Smoke test: ask for the action dict; do not render the PDF to keep the test light
        action_dict = action.report_action(self.project)
        self.assertIsInstance(action_dict, dict)
