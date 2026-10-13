# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import SQL


@tagged("post_install", "-at_install")
class TestOpenIssueMail(TransactionCase):
    """BUSINESS-011: the submission mail of an Open Issue is rendered on the Open Issue itself."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.manager = cls.env["res.partner"].create({"name": "BUSINESS-011 manager", "email": "pm011@example.com"})
        cls.project = cls.env["business.project"].create(
            {"name": "BUSINESS-011 project", "project_manager_id": cls.manager.id}
        )
        cls.other_project = cls.env["business.project"].create(
            {"name": "BUSINESS-011 other project", "project_manager_id": cls.manager.id}
        )

    def _submission_mails(self, model, res_id):
        return self.env["mail.mail"].search([("model", "=", model), ("res_id", "=", res_id)])

    def _assert_open_issue_mail(self, open_issue):
        mails = self._submission_mails("business.open.issue", open_issue.id)
        self.assertEqual(len(mails), 1)
        self.assertIn(open_issue.name, str(mails.body_html))
        self.assertIn(self.project.name, str(mails.body_html))
        self.assertEqual(mails.recipient_ids, self.manager)

    def test_open_issue_create_without_id_collision(self):
        # no business.issue shares the id of the new open issue
        self.env.cr.execute(SQL("SELECT COALESCE(MAX(id), 0) FROM business_issue"))
        max_issue_id = self.env.cr.fetchone()[0]
        self.env.cr.execute(SQL("SELECT COALESCE(MAX(id), 0) FROM business_open_issue"))
        target = max(max_issue_id, self.env.cr.fetchone()[0]) + 1
        self.env.cr.execute(SQL("SELECT setval('business_open_issue_id_seq', %s, false)", target))

        open_issue = self.env["business.open.issue"].create(
            {"name": "BUSINESS-011 open", "project_id": self.project.id}
        )

        self.assertEqual(open_issue.id, target)
        self.assertFalse(self.env["business.issue"].browse(open_issue.id).exists())
        self._assert_open_issue_mail(open_issue)

    def test_open_issue_create_with_id_collision(self):
        # a business.issue of another project shares the id of the new open issue
        self.env.cr.execute(SQL("SELECT COALESCE(MAX(id), 0) FROM business_issue"))
        max_issue_id = self.env.cr.fetchone()[0]
        self.env.cr.execute(SQL("SELECT COALESCE(MAX(id), 0) FROM business_open_issue"))
        target = max(max_issue_id, self.env.cr.fetchone()[0]) + 1
        self.env.cr.execute(SQL("SELECT setval('business_issue_id_seq', %s, false)", target))
        self.env.cr.execute(SQL("SELECT setval('business_open_issue_id_seq', %s, false)", target))

        issue = self.env["business.issue"].create(
            {"name": "BUSINESS-011 unrelated", "project_id": self.other_project.id}
        )
        open_issue = self.env["business.open.issue"].create(
            {"name": "BUSINESS-011 open", "project_id": self.project.id}
        )

        self.assertEqual(issue.id, open_issue.id)
        self._assert_open_issue_mail(open_issue)
        # the business.issue keeps only its own submission mail
        issue_mails = self._submission_mails("business.issue", issue.id)
        self.assertEqual(len(issue_mails), 1)
        self.assertIn(issue.name, str(issue_mails.body_html))
        self.assertNotIn(open_issue.name, str(issue_mails.body_html))

    def test_issue_submission_mail_unchanged(self):
        issue = self.env["business.issue"].create({"name": "BUSINESS-011 issue", "project_id": self.project.id})
        mails = self._submission_mails("business.issue", issue.id)
        self.assertEqual(len(mails), 1)
        self.assertIn(issue.name, str(mails.body_html))
        self.assertEqual(mails.recipient_ids, self.manager)
