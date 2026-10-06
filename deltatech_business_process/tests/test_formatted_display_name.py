# © 2026 Deltatech
# See README.rst file on addons root folder for license details

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.deltatech_business_process.models.business_issue import BusinessIssue


@tagged("post_install", "-at_install")
class TestFormattedDisplayName(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        partner = cls.env["res.partner"].create({"name": "FDN Tester"})
        area = cls.env["business.area"].create({"name": "FDN Area", "responsible_id": partner.id})
        group = cls.env["business.process.group"].create({"name": "FDN Group", "area_id": area.id})
        cls.project = cls.env["business.project"].create(
            {"name": "FDN Project", "code": "FDNPRJ", "customer_id": partner.id, "project_type": "remote"}
        )
        cls.process = cls.env["business.process"].create(
            {
                "name": "FDN Order to Cash",
                "code": "FDNPROC",
                "area_id": area.id,
                "process_group_id": group.id,
                "project_id": cls.project.id,
                "responsible_id": partner.id,
                "customer_id": partner.id,
            }
        )
        cls.step = cls.env["business.process.step"].create(
            {"name": "FDN Create SO", "code": "FDNST", "process_id": cls.process.id}
        )
        dev_type = cls.env["business.development.type"].create({"name": "FDN Type"})
        cls.development = cls.env["business.development"].create(
            {"name": "FDN Development", "code": "FDNDEV", "area_id": area.id, "type_id": dev_type.id}
        )
        with patch.object(BusinessIssue, "send_issue_mail", autospec=True):
            cls.issue = cls.env["business.issue"].create(
                {"name": "FDN Issue", "code": "FDNISS", "project_id": cls.project.id}
            )
        cls.migration = cls.env["business.migration"].create(
            {"name": "FDN Migration", "code": "FDNMIG", "project_id": cls.project.id}
        )
        cls.transaction = cls.env["business.transaction"].create({"name": "FDN Transaction", "code": "FDNTR"})

    def _records(self):
        return [
            (self.project, "FDNPRJ", "FDN Project"),
            (self.process, "FDNPROC", "FDN Order to Cash"),
            (self.development, "FDNDEV", "FDN Development"),
            (self.issue, "FDNISS", "FDN Issue"),
            (self.migration, "FDNMIG", "FDN Migration"),
            (self.transaction, "FDNTR", "FDN Transaction"),
        ]

    def test_plain_display_name_unchanged(self):
        for record, code, name in [*self._records(), (self.step, "FDNST", "FDN Create SO")]:
            self.assertEqual(record.display_name, f"[{code}] {name}")

    def test_formatted_display_name(self):
        for record, code, name in self._records():
            self.assertEqual(record.with_context(formatted_display_name=True).display_name, f"{name}\t--{code}--")
        # the step also shows the code of its process: step codes repeat between imported processes
        self.assertEqual(
            self.step.with_context(formatted_display_name=True).display_name, "FDN Create SO\t--FDNST · FDNPROC--"
        )

    def test_without_code(self):
        self.transaction.code = False
        self.assertEqual(self.transaction.display_name, "FDN Transaction")
        self.assertEqual(self.transaction.with_context(formatted_display_name=True).display_name, "FDN Transaction")
        # a step without code still shows its process code
        self.step.code = False
        self.assertEqual(self.step.display_name, "FDN Create SO")
        self.assertEqual(self.step.with_context(formatted_display_name=True).display_name, "FDN Create SO\t--FDNPROC--")

    def test_web_name_search_returns_both_forms(self):
        result = self.env["business.transaction"].web_name_search("FDNTR", {"display_name": {}})
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["display_name"], "[FDNTR] FDN Transaction")
        self.assertEqual(result[0]["__formatted_display_name"], "FDN Transaction\t--FDNTR--")

    def test_name_search_by_code(self):
        for record, code, _name in [*self._records(), (self.step, "FDNST", "FDN Create SO")]:
            ids = [rid for rid, _label in record.name_search(code)]
            self.assertIn(record.id, ids, f"{record._name}: name_search({code!r}) should find the record")
