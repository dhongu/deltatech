from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPosPriceLock(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env["pos.config"].create({"name": "Price Lock Register"})

    def test_lock_is_off_by_default(self):
        self.assertFalse(self.config.lock_price_for_managers)

    def test_lock_is_loaded_in_the_register(self):
        """pos.config loads all its fields in the register, so the flag reaches the browser."""
        self.assertFalse(self.env["pos.config"]._load_pos_data_fields(self.config))

    def test_settings_write_the_register(self):
        settings = self.env["res.config.settings"].create(
            {"pos_config_id": self.config.id, "pos_restrict_price_control": True, "pos_lock_price_for_managers": True}
        )
        settings.execute()
        self.assertTrue(self.config.restrict_price_control)
        self.assertTrue(self.config.lock_price_for_managers)
