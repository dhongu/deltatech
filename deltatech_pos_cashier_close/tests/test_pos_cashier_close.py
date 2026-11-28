from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPosCashierClose(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env["pos.config"].create({"name": "Cashier Close Register"})

    def test_cashiers_close_by_default(self):
        """Installing the module is the decision: the option starts on."""
        self.assertTrue(self.config.cashier_can_close)

    def test_option_is_loaded_in_the_register(self):
        """pos.config loads all its fields in the register, so the flag reaches the browser."""
        self.assertFalse(self.env["pos.config"]._load_pos_data_fields(self.config))

    def test_settings_write_the_register(self):
        settings = self.env["res.config.settings"].create(
            {"pos_config_id": self.config.id, "pos_cashier_can_close": False}
        )
        settings.execute()
        self.assertFalse(self.config.cashier_can_close)
