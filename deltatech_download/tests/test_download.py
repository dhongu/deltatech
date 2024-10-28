import base64

from odoo.tests.common import TransactionCase


class TestWizardDownloadFile(TransactionCase):
    def setUp(self):
        super().setUp()
        self.wizard = self.env["wizard.download.file"].create(
            {
                "file_name": "test_file.txt",
                "data_file": base64.b64encode(b"Test file content"),
            }
        )

    def test_do_download_file(self):
        action = self.wizard.do_download_file()

        expected_url = f"/web/content?model=wizard.download.file&download=True&field=data_file&id={self.wizard.id}&filename=test_file.txt"  # noq E501

        self.assertEqual(action["type"], "ir.actions.act_url")
        self.assertEqual(action["url"], expected_url)
        self.assertEqual(action["target"], "new")
