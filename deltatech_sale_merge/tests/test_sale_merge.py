# ©  2026 Deltatech
# See README.rst file on addons root folder for license details

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.sale.tests.common import SaleCommon


@tagged("post_install", "-at_install")
class TestSaleMerge(SaleCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_b = cls.env["product.product"].create({"name": "Merge B", "list_price": 20.0})

    def _order(self, lines, **kwargs):
        vals = {
            "partner_id": self.partner.id,
            "order_line": [Command.create({"product_id": p.id, "product_uom_qty": q}) for p, q in lines],
        }
        vals.update(kwargs)
        return self.env["sale.order"].create(vals)

    def _merge(self, orders, **kwargs):
        wizard = (
            self.env["sale.order.merge"]
            .with_context(active_model="sale.order", active_ids=orders.ids)
            .create({"order_ids": [Command.set(orders.ids)], **kwargs})
        )
        wizard.action_merge()
        return wizard

    def test_sum_into_oldest(self):
        so1 = self._order([(self.product, 1), (self.product_b, 2)])
        so2 = self._order([(self.product, 3)])
        self._merge(so1 | so2)
        lines = so1.order_line
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines.filtered(lambda line: line.product_id == self.product).product_uom_qty, 4)
        self.assertEqual(so2.state, "cancel")
        self.assertEqual(so2.merged_into_id, so1)
        self.assertEqual(so1.merged_from_ids, so2)
        self.assertEqual(len(so2.order_line), 1, "the source keeps its lines")

    def test_keep_all_lines(self):
        so1 = self._order([(self.product, 1)])
        so2 = self._order([(self.product, 3)])
        self._merge(so1 | so2, line_mode="keep")
        self.assertEqual(sorted(so1.order_line.mapped("product_uom_qty")), [1, 3])

    def test_different_price_not_added(self):
        so1 = self._order([(self.product, 1)])
        so2 = self._order([(self.product, 1)])
        so2.order_line.price_unit = 99.0
        self._merge(so1 | so2)
        self.assertEqual(len(so1.order_line), 2)

    def test_new_target(self):
        so1 = self._order([(self.product, 1)], origin="OPP1")
        so2 = self._order([(self.product, 2)], origin="OPP2")
        self._merge(so1 | so2, target_mode="new")
        new = (so1 | so2).merged_into_id
        self.assertEqual(len(new), 1)
        self.assertNotIn(new, so1 | so2)
        self.assertEqual(new.state, "draft")
        self.assertEqual(new.order_line.product_uom_qty, 3)
        self.assertEqual(new.origin, "OPP1, OPP2")
        self.assertEqual((so1 | so2).mapped("state"), ["cancel", "cancel"])

    def test_selected_target_and_sections(self):
        so1 = self._order([(self.product, 1)])
        so2 = self._order([(self.product_b, 1)])
        self._merge(so1 | so2, target_mode="selected", target_order_id=so2.id, add_sections=True)
        self.assertEqual(so1.state, "cancel")
        self.assertEqual(so2.state, "draft")
        sections = so2.order_line.filtered(lambda line: line.display_type == "line_section")
        self.assertEqual(sections.mapped("name"), [so1.name])

    def test_different_partner_blocked(self):
        so1 = self._order([(self.product, 1)])
        so2 = self._order([(self.product, 1)], partner_id=self.env["res.partner"].create({"name": "Other"}).id)
        with self.assertRaises(UserError):
            self._merge(so1 | so2)
        self.assertEqual(so1.state, "draft")

    def test_confirmed_blocked(self):
        so1 = self._order([(self.product, 1)])
        so2 = self._order([(self.product, 1)])
        so2.action_confirm()
        with self.assertRaises(UserError):
            self._merge(so1 | so2)

    def test_single_order_blocked(self):
        so1 = self._order([(self.product, 1)])
        with self.assertRaises(UserError):
            self._merge(so1)

    def test_different_taxes_not_added(self):
        so1 = self._order([(self.product, 1)])
        so2 = self._order([(self.product, 1)])
        tax = self.env["account.tax"].create({"name": "Merge tax", "amount": 10.0, "type_tax_use": "sale"})
        so2.order_line.tax_ids = tax
        so1.order_line.tax_ids = False
        self._merge(so1 | so2)
        self.assertEqual(len(so1.order_line), 2)

    def test_signed_blocked(self):
        so1 = self._order([(self.product, 1)])
        so2 = self._order([(self.product, 1)])
        png = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR4nGNgYGD4DwABBAEAHnOcQAAAAABJRU5ErkJggg=="
        so2.signature = png
        with self.assertRaises(UserError):
            self._merge(so1 | so2)
        self.assertEqual(so1.state, "draft")

    def test_online_payment_started_blocked(self):
        so1 = self._order([(self.product, 1)])
        so2 = self._order([(self.product, 1)])
        provider = self.env["payment.provider"].create({"name": "Merge test", "code": "none"})
        method = self.env["payment.method"].create({"name": "Merge method", "code": "mergetest"})
        tx = self.env["payment.transaction"].create(
            {
                "provider_id": provider.id,
                "payment_method_id": method.id,
                "amount": 1.0,
                "currency_id": so2.currency_id.id,
                "partner_id": self.partner.id,
                "reference": "MERGE-TEST",
                "state": "pending",
            }
        )
        so2.transaction_ids = [Command.set(tx.ids)]
        with self.assertRaises(UserError):
            self._merge(so1 | so2)
        self.assertEqual(so1.state, "draft")

    def test_different_company_blocked(self):
        so1 = self._order([(self.product, 1)])
        company = self.env["res.company"].create({"name": "Other merge company"})
        so2 = self._order([(self.product, 1)], company_id=company.id)
        with self.assertRaises(UserError):
            self._merge(so1 | so2)
        self.assertEqual(so1.state, "draft")
