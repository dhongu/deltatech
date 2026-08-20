from unittest.mock import patch

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPosPriceSync(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env["pos.config"].create({"name": "Test PRICE_SYNCHRONISATION"})
        cls.pos_config.open_ui()
        cls.pos_config.current_session_id.set_opening_control(0, "")
        cls.product = cls.env["product.product"].create(
            {
                "name": "Price Sync Product",
                "available_in_pos": True,
                "list_price": 10.0,
            }
        )

    def test_list_price_change_notifies_open_session(self):
        with patch.object(type(self.pos_config), "_notify") as notify_mock:
            self.product.product_tmpl_id.write({"list_price": 25.0})
        notify_mock.assert_called_once()
        name, message = notify_mock.call_args.args
        self.assertEqual(name, "PRICE_SYNCHRONISATION")
        data = message["product.template"]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["id"], self.product.product_tmpl_id.id)
        self.assertEqual(data[0]["list_price"], 25.0)

    def test_standard_price_change_notifies_open_session(self):
        with patch.object(type(self.pos_config), "_notify") as notify_mock:
            self.product.product_tmpl_id.write({"standard_price": 5.0})
        notify_mock.assert_called_once()

    def test_unrelated_field_change_does_not_notify(self):
        with patch.object(type(self.pos_config), "_notify") as notify_mock:
            self.product.product_tmpl_id.write({"name": "Renamed Product"})
        notify_mock.assert_not_called()

    def test_product_not_available_in_pos_is_not_notified(self):
        other = self.env["product.product"].create({"name": "Not In POS", "available_in_pos": False, "list_price": 5.0})
        with patch.object(type(self.pos_config), "_notify") as notify_mock:
            other.product_tmpl_id.write({"list_price": 15.0})
        notify_mock.assert_not_called()

    def test_no_open_session_does_not_notify(self):
        self.pos_config.current_session_id.action_pos_session_closing_control()
        with patch.object(type(self.pos_config), "_notify") as notify_mock:
            self.product.product_tmpl_id.write({"list_price": 30.0})
        notify_mock.assert_not_called()
