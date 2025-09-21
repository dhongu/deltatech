# ©  2024 Deltatech
#              Dorin Hongu <dhongu(@)gmail(.)com
# See README.rst file on addons root folder for license details


from odoo.tests.common import TransactionCase


class TestNeutralized(TransactionCase):
    def setUp(self):
        super().setUp()
        self.config_settings = self.env["res.config.settings"].create({"database_is_neutralized": True})

    def test_neutralized(self):
        self.assertTrue(self.config_settings.database_is_neutralized)
