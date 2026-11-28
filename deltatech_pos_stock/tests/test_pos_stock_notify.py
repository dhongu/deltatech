from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestPosStockNotify(TransactionCase):
    """Which open registers are told about a stock change, and about which products."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_b = cls.env["res.company"].create({"name": "POS Stock Company B"})
        cls.shared = cls.env["product.template"].create(
            {"name": "Shared POS product", "is_storable": True, "available_in_pos": True}
        )
        cls.product_b = cls.env["product.template"].create(
            {
                "name": "Company B POS product",
                "is_storable": True,
                "available_in_pos": True,
                "company_id": cls.company_b.id,
            }
        )
        cls.config = cls.env["pos.config"].create({"name": "Notify Test Register"})
        cls.session = cls.env["pos.session"].create({"config_id": cls.config.id})
        cls.session.state = "opened"

    def _notified(self, templates):
        sent = {}

        def fake_notify(config, name, payload):
            sent[config.id] = {rec["id"] for rec in payload["product.template"]}

        with patch.object(type(self.env["pos.config"]), "_notify", fake_notify, create=True):
            templates._notify_pos_stock_change()
        return sent

    def test_mixed_batch_reaches_registers_selling_the_shared_product(self):
        # POSSTOCK-001: a batch with a shared product and a product of another company
        # must still reach the registers of this company, for the shared product only
        sent = self._notified(self.shared | self.product_b)
        self.assertIn(self.config.id, sent)
        self.assertEqual(sent[self.config.id], {self.shared.id})

    def test_other_company_products_are_not_sent(self):
        sent = self._notified(self.product_b)
        self.assertNotIn(self.config.id, sent)
