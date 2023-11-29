# ©  2023 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests.common import TransactionCase


class TestObjectHistory(TransactionCase):
    def setUp(self):
        super().setUp()
        self.partner1 = self.env["res.partner"].create(
            {
                "name": "Partner 1",
                "company_type": "company",
            }
        )

    def test_history(self):
        wizard = (
            self.env["history.add.wizard"]
            .with_context(active_id=self.partner1.id, active_model="res.partner")
            .create(
                {
                    "name": "TestName",
                    "description": "Test Description",
                }
            )
        )
        wizard.add_history()
        wizard.name = "TestName2"
        wizard.description = "Test description 2"
        wizard.add_history()
        histories = self.env["object.history"].search(
            [("res_id", "=", self.partner1.id), ("res_model", "=", "res.partner")]
        )
        self.assertEqual(len(histories), 2)
