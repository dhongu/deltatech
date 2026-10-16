from odoo.tests.common import TransactionCase
from odoo.tools import BinaryBytes


class TestWizardDownloadFile(TransactionCase):
    def setUp(self):
        super().setUp()
        self.wizard = self.env["wizard.download.file"].create(
            {
                "file_name": "test_file.txt",
                "data_file": BinaryBytes(b"Test file content"),
            }
        )

    def test_do_download_file(self):
        action = self.wizard.do_download_file()

        expected_url = f"/web/content?model=wizard.download.file&download=True&field=data_file&id={self.wizard.id}&filename=test_file.txt"  # noqa E501

        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(action["url"], expected_url)
        self.assertEqual(action["target"], "new")
        self.assertEqual(self.wizard.data_file.content, b"Test file content")

    def test_direct_download_in_action(self):
        report = self.env["ir.actions.report"].search([("report_type", "=", "qweb-pdf")], limit=1)
        if not report:
            report = self.env["ir.actions.report"].create(
                {
                    "name": "Test Report",
                    "model": "res.partner",
                    "report_type": "qweb-pdf",
                    "report_name": "base.test_report",
                }
            )
        report.direct_download = True
        partner = self.env.user.partner_id
        action = report.with_context(discard_logo_check=True).report_action(partner)
        self.assertTrue(action["direct_download"])

        report.direct_download = False
        action = report.with_context(discard_logo_check=True).report_action(partner)
        self.assertFalse(action["direct_download"])

    def test_direct_download_readable(self):
        self.assertIn("direct_download", self.env["ir.actions.report"]._get_readable_fields())
