# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestBusinessProjectCreateMulti(TransactionCase):
    def test_create_multi_creates_all_projects_with_code(self):
        partner = self.env["res.partner"].create({"name": "Tester Multi"})
        projects = self.env["business.project"].create(
            [
                {"name": "Project A", "customer_id": partner.id, "project_type": "remote"},
                {"name": "Project B", "customer_id": partner.id, "project_type": "remote"},
            ]
        )
        self.assertEqual(len(projects), 2)
        self.assertEqual(sorted(projects.mapped("name")), ["Project A", "Project B"])
        self.assertTrue(all(projects.mapped("code")))
        self.assertNotEqual(projects[0].code, projects[1].code)
        found = self.env["business.project"].search([("customer_id", "=", partner.id)])
        self.assertEqual(found, projects)
