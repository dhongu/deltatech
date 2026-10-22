# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPriceChangeLog(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env["product.template"].create({"name": "Test price change", "list_price": 100})
        cls.Log = cls.env["product.price.change.log"]

    def _logs(self):
        return self.Log.search([("product_tmpl_id", "=", self.product.id)])

    def test_one_log_per_day(self):
        self.product.list_price = 110
        self.product.list_price = 120
        logs = self._logs()
        self.assertEqual(len(logs), 1)
        self.assertEqual((logs.old_price, logs.new_price), (100, 120))

    def test_back_to_previous_price_removes_log(self):
        self.product.list_price = 110
        self.product.list_price = 100
        self.assertFalse(self._logs())

    def test_variant_price_is_logged(self):
        self.product.product_variant_id.lst_price = 90
        self.assertEqual(self._logs().new_price, 90)

    def test_document_loads_and_closes_logs(self):
        self.product.list_price = 130
        change = self.env["product.price.change"].create({"type": "log"})
        change.action_load_price_changes()
        self.assertEqual(len(change.line_ids), 1)
        line = change.line_ids
        self.assertEqual((line.product_template_id, line.old_price, line.new_price), (self.product, 100, 130))
        self.assertEqual(self._logs().price_change_id, change)

        # a change made while the document is still a draft updates its line
        self.product.list_price = 140
        self.assertEqual(line.new_price, 140)

        change.action_confirm()
        self.assertEqual(change.state, "done")
        self.assertNotEqual(change.name, "/")
        self.assertEqual(self.product.list_price, 140)

        # after the confirmation the same day starts a new log
        self.product.list_price = 150
        logs = self._logs()
        self.assertEqual(len(logs), 2)
        new_log = logs.filtered(lambda log: not log.price_change_id)
        self.assertEqual((new_log.old_price, new_log.new_price), (140, 150))

        # a second document takes only the log that is not in a document
        other = self.env["product.price.change"].create({"type": "log"})
        other.action_load_price_changes()
        self.assertEqual(other.line_ids.log_id, new_log)

    def test_document_price_is_not_logged(self):
        change = self.env["product.price.change"].create(
            {
                "type": "product",
                "use_product_template": True,
                "line_ids": [(0, 0, {"product_template_id": self.product.id, "old_price": 100, "new_price": 105})],
            }
        )
        change.action_confirm()
        self.assertEqual(self.product.list_price, 105)
        self.assertFalse(self._logs())

    def test_report_renders(self):
        self.product.list_price = 130
        change = self.env["product.price.change"].create({"type": "log"})
        change.action_load_price_changes()
        html = self.env["ir.actions.report"]._render_qweb_html("deltatech_price_change.report_pricechange", change.ids)[
            0
        ]
        self.assertIn(b"Test price change", html)
