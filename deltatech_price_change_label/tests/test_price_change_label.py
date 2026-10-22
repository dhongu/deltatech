# ©  2026 Terrabit
# See README.rst file on addons root folder for license details

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPriceChangeLabel(TransactionCase):
    def test_label_lines_from_document(self):
        product = self.env["product.template"].create({"name": "Test label", "list_price": 100})
        product.list_price = 110
        change = self.env["product.price.change"].create({"type": "log"})
        change.action_load_price_changes()
        action = change.action_print_labels()
        wizard = (
            self.env["product.product.label"]
            .with_context(**action["context"])
            .create({"layout_id": self.env.ref("deltatech_product_labels.report_product_product_label").id})
        )
        self.assertEqual(wizard.label_lines.product_id, product.product_variant_id)
