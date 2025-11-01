# © 2025 Deltatech
# See README.rst file on addons root folder for license details

import base64

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCronCleanXMLAttachments(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Minimal partner and invoice to attach XMLs to
        cls.partner = cls.env["res.partner"].create({"name": "XML Customer"})
        cls.move = cls.env["account.move"].create(
            {
                "move_type": "out_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": cls.env.cr.now(),
            }
        )

    def _create_xml(self, name: str):
        return self.env["ir.attachment"].create(
            {
                "name": name,
                "res_model": "account.move",
                "res_id": self.move.id,
                "type": "binary",
                "datas": base64.b64encode(b"<xml>test</xml>"),
                "mimetype": "application/xml",
            }
        )

    def test_xml_cron_dry_run_and_delete(self):
        # Create three duplicate XML attachments (same name) and one unrelated
        dup1 = self._create_xml("INV_UBL.xml")
        dup2 = self._create_xml("INV_UBL.xml")
        dup3 = self._create_xml("INV_UBL.xml")
        single = self._create_xml("SINGLE.xml")

        # Dry run should not delete anything
        self.env["account.move"].cron_clean_xml_attachments(
            limit=10, duplicates=1, max_attachments_to_delete=50, dry_run=True
        )
        self.assertTrue(dup1.exists())
        self.assertTrue(dup2.exists())
        self.assertTrue(dup3.exists())
        self.assertTrue(single.exists())

        # Real run with a cap should delete at most the cap number of duplicates
        self.env["account.move"].cron_clean_xml_attachments(
            limit=10, duplicates=1, max_attachments_to_delete=2, dry_run=False
        )

        # Only one of the duplicate set should remain, and the unrelated stays
        remaining_dups = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "account.move"),
                ("res_id", "=", self.move.id),
                ("name", "=", "INV_UBL.xml"),
                ("mimetype", "=", "application/xml"),
            ]
        )
        self.assertEqual(len(remaining_dups), 1)
        self.assertTrue(single.exists())
